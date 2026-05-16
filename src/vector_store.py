import os
import logging
import chromadb
from chromadb.utils import embedding_functions
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import streamlit as st

from src.config import Config
from src.models import JobDescriptions, EmployeeFeedback

logger = logging.getLogger(__name__)


@st.cache_resource
def _get_chroma_client(db_path):
    return chromadb.PersistentClient(path=db_path)

@st.cache_resource
def _get_embedding_func(model_name):
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)

class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        try:
            self.client = _get_chroma_client(Config.CHROMA_DB_PATH)
            self.embedding_func = _get_embedding_func(Config.EMBEDDING_MODEL)

            self.collection = self.client.get_or_create_collection(
                name="pms_data",
                embedding_function=self.embedding_func
            )

            doc_count = self.collection.count()
            logger.info(f"Vektör DB Bağlandı. Mevcut Döküman Sayısı: {doc_count}")

            if doc_count == 0:
                logger.info("⚠️ Veritabanı boş görünüyor. Otomatik veri yükleme başlatılıyor...")
                self.refresh_data()

        except Exception as e:
            logger.error(f"Vektör DB Başlatma Hatası: {str(e)}")
            self.collection = None

    # ──────────────────────────────────────────────────────────────────
    # Yardımcı: SQL session
    # ──────────────────────────────────────────────────────────────────

    def _get_sql_session(self):
        """SQLAlchemy oturumu oluşturur ve döner."""
        engine = create_engine(Config.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        return Session()

    # ──────────────────────────────────────────────────────────────────
    # refresh_data — artık SADECE SQL'den beslenir (Word/Excel YOK)
    # ──────────────────────────────────────────────────────────────────

    def refresh_data(self):
        """
        SQL veritabanındaki JobDescriptions ve EmployeeFeedback tablolarını
        okuyarak ChromaDB koleksiyonunu sıfırdan indeksler.
        Her çalıştırmada koleksiyon önce temizlenir (idempotent).
        """
        if not self.collection:
            logger.warning("Koleksiyon bulunamadı, yeniden başlatma deneniyor...")
            self.initialize()
            if not self.collection:
                logger.error("Koleksiyon başlatılamadığı için refresh yapılamıyor.")
                return

        # SQL'den veri çek
        try:
            sql_session = self._get_sql_session()
            job_descriptions = sql_session.query(JobDescriptions).all()
            feedbacks        = sql_session.query(EmployeeFeedback).all()
            sql_session.close()
        except Exception as e:
            logger.error(f"SQL sorgu hatası (refresh_data): {e}")
            return

        documents = []
        metadatas = []
        ids       = []

        # ── JobDescriptions → ChromaDB ────────────────────────────────
        for jd in job_descriptions:
            parts = []
            if jd.position_name:
                parts.append(f"Pozisyon: {jd.position_name}")
            if jd.responsibilities:
                parts.append(f"Ana Sorumluluklar:\n{jd.responsibilities}")
            if jd.technical_requirements:
                parts.append(f"Teknik Gereksinimler:\n{jd.technical_requirements}")
            if jd.competencies:
                parts.append(f"Yetkinlikler:\n{jd.competencies}")

            if not parts:
                continue

            documents.append("\n\n".join(parts))
            metadatas.append({
                "type":          "job_description",
                "position_name": jd.position_name or "",
                "source":        "JobDescriptions"
            })
            ids.append(f"jd_{jd.id}_{os.urandom(3).hex()}")

        # ── EmployeeFeedback → ChromaDB ───────────────────────────────
        for fb in feedbacks:
            parts = []
            if fb.yil:
                parts.append(f"[{fb.yil} Yılı Genel Değerlendirmesi]")
            else:
                parts.append("[Genel Değerlendirme]")
            
            if fb.harf_notu:
                parts.append(f"Harf Notu: {fb.harf_notu}")
            if fb.genel_degerlendirme:
                parts.append(f"Genel Performans:\n{fb.genel_degerlendirme}")
            if fb.guclu_alanlar:
                parts.append(f"Güçlü Alanlar:\n{fb.guclu_alanlar}")
            if fb.gelisim_alanlari:
                parts.append(f"Gelişim Alanları:\n{fb.gelisim_alanlari}")
            if fb.gelecek_beklentileri:
                parts.append(f"Gelecek Beklentileri:\n{fb.gelecek_beklentileri}")

            # Eğer not ve içerik yoksa atla
            if len(parts) <= 1:
                continue

            text = "\n\n".join(parts)
            documents.append(text)
            metadatas.append({
                "type":          "feedback",
                "feedback_type": "Yıllık Değerlendirme",
                "yil":           str(fb.yil) if fb.yil else "",
                "sicil_no":      str(fb.employee_sicil) if fb.employee_sicil else "",
                "source":        "EmployeeFeedback"
            })
            ids.append(f"fb_{fb.id}_{os.urandom(3).hex()}")

        if not documents:
            logger.warning(
                "SQL'de indekslenecek kayıt bulunamadı "
                "(JobDescriptions ve EmployeeFeedback tabloları boş)."
            )
            return

        try:
            # Eski verileri temizle
            existing_ids = self.collection.get()['ids']
            if existing_ids:
                self.collection.delete(ids=existing_ids)
                logger.info("Eski ChromaDB verileri temizlendi.")

            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
            logger.info(
                f"✅ {len(job_descriptions)} görev tanımı + "
                f"{len(feedbacks)} geri bildirim ChromaDB'ye eklendi."
            )
        except Exception as e:
            logger.error(f"Veri İndeksleme Hatası: {str(e)}")

    # ──────────────────────────────────────────────────────────────────
    # where filtresi yardımcısı
    # ──────────────────────────────────────────────────────────────────

    def _build_where_clause(self, sicil_no=None, position_name=None):
        """
        sicil_no ve/veya position_name'e göre ChromaDB metadata filtresi üretir.
        - Yalnızca sicil_no  → feedback belgelerini sicile göre daraltır.
        - Yalnızca position_name → job_description belgelerini pozisyona göre daraltır.
        - İkisi birden → her iki türü de kapsayan OR filtresi döner.
        - Hiçbiri verilmezse → None (filtre uygulanmaz).
        """
        if sicil_no and position_name:
            return {
                "$or": [
                    {"$and": [
                        {"type":      {"$eq": "feedback"}},
                        {"sicil_no":  {"$eq": str(sicil_no)}}
                    ]},
                    {"$and": [
                        {"type":          {"$eq": "job_description"}},
                        {"position_name": {"$eq": position_name}}
                    ]}
                ]
            }
        if sicil_no:
            return {
                "$and": [
                    {"type":     {"$eq": "feedback"}},
                    {"sicil_no": {"$eq": str(sicil_no)}}
                ]
            }
        if position_name:
            return {
                "$and": [
                    {"type":          {"$eq": "job_description"}},
                    {"position_name": {"$eq": position_name}}
                ]
            }
        return None

    # ──────────────────────────────────────────────────────────────────
    # get_context — opsiyonel sicil/pozisyon filtresiyle metin döner
    # ──────────────────────────────────────────────────────────────────

    def get_context(self, query, top_k=6, sicil_no=None, position_name=None):
        """
        Sorguya en uygun bağlamı metin olarak getirir.

        sicil_no    → yalnızca o çalışana ait geri bildirimler.
        position_name → yalnızca o pozisyonun görev tanımı.
        İkisi birden  → her ikisini de kapsar.
        Hiçbiri       → koleksiyonun tamamında arama (mevcut davranış).
        """
        if not self.collection:
            self.initialize()
            if not self.collection:
                return "HATA: Vektör veritabanı (context) şu an erişilemez durumda."

        doc_count = self.collection.count()
        if doc_count == 0:
            return "BİLGİ: Vektör veritabanında henüz yüklenmiş bir döküman yok."

        try:
            where = self._build_where_clause(sicil_no, position_name)
            query_kwargs = dict(query_texts=[query], n_results=min(top_k, doc_count))
            if where:
                query_kwargs["where"] = where

            results = self.collection.query(**query_kwargs)

            context = ""
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    meta  = results['metadatas'][0][i]
                    dtype = meta.get('type', 'Bilinmeyen').upper()
                    label = (
                        meta.get('position_name')
                        or meta.get('feedback_type')
                        or meta.get('source', '-')
                    )
                    context += f"📌 [{dtype} | {label}]\n{doc}\n{'-'*30}\n"
                return context
            else:
                return "BİLGİ: Bu sorgu için veritabanında eşleşen veri bulunamadı."

        except Exception as e:
            logger.error(f"Sorgulama hatası: {e}")
            return f"HATA: Veritabanı sorgusu sırasında teknik bir sorun oluştu: {str(e)}"

    # ──────────────────────────────────────────────────────────────────
    # get_evidence — opsiyonel sicil/pozisyon filtresiyle yapısal liste
    # ──────────────────────────────────────────────────────────────────

    def get_evidence(self, query, top_k=6, sicil_no=None, position_name=None):
        """
        Sorguya en uygun kanıtları yapısal liste olarak getirir.
        Filtre parametreleri get_context ile aynı semantiğe sahiptir.
        """
        if not self.collection:
            self.initialize()
            if not self.collection:
                return []

        doc_count = self.collection.count()
        if doc_count == 0:
            return []

        try:
            where = self._build_where_clause(sicil_no, position_name)
            query_kwargs = dict(query_texts=[query], n_results=min(top_k, doc_count))
            if where:
                query_kwargs["where"] = where

            results = self.collection.query(**query_kwargs)

            evidence = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    evidence.append({
                        "id":       results['ids'][0][i],
                        "content":  results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "score":    (
                            results['distances'][0][i]
                            if 'distances' in results and results['distances']
                            else 0.0
                        )
                    })
            return evidence

        except Exception as e:
            logger.error(f"Kanıt toplama hatası: {e}")
            return []