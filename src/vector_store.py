import os
import chromadb
from chromadb.utils import embedding_functions
from src.config import Config
from src.data_loader import DataLoader
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        try:
            self.client = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
            
            # SentenceTransformer kullanarak config'deki modeli yüklüyoruz
            self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=Config.EMBEDDING_MODEL
            )
            
            self.collection = self.client.get_or_create_collection(
                name="pms_data",
                embedding_function=self.embedding_func
            )
            
            # İlk başlatmada veri kontrolü
            doc_count = self.collection.count()
            logger.info(f"Vektör DB Bağlandı. Mevcut Döküman Sayısı: {doc_count}")
            
            if doc_count == 0:
                logger.info("⚠️ Veritabanı boş görünüyor. Otomatik veri yükleme başlatılıyor...")
                self.refresh_data()
                
        except Exception as e:
            logger.error(f"Vektör DB Başlatma Hatası: {str(e)}")
            self.collection = None

    def refresh_data(self):
        """Verileri kaynaktan okur ve yeniden indeksler."""
        if not self.collection:
            logger.warning("Koleksiyon bulunamadı, yeniden başlatma deneniyor...")
            self.initialize()
            if not self.collection:
                logger.error("Koleksiyon başlatılamadığı için refresh yapılamıyor.")
                return

        loader = DataLoader()
        chunked_docs = loader.get_chunked_documents()
        
        if not chunked_docs:
            logger.warning("Yüklenecek veri bulunamadı.")
            return

        try:
             # Öncekileri sil
            ids_to_delete = self.collection.get()['ids']
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info("Eski veriler temizlendi.")
            
            ids = [f"doc_{i}_{os.urandom(4).hex()}" for i in range(len(chunked_docs))]
            documents = [doc['page_content'] for doc in chunked_docs]
            metadatas = [doc['metadata'] for doc in chunked_docs]
            
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"✅ {len(documents)} parça veri başarıyla eklendi.")
            
        except Exception as e:
            logger.error(f"Veri İndeksleme Hatası: {str(e)}")

    def get_context(self, query, top_k=6): # top_k'yı biraz artıralım
        """Sorguya en uygun bağlamı getirir."""
        if not self.collection:
            self.initialize()
            if not self.collection:
                return "HATA: Vektör veritabanı (context) şu an erişilemez durumda."

        doc_count = self.collection.count()
        if doc_count == 0:
            return "BİLGİ: Vektör veritabanında henüz yüklenmiş bir döküman yok."

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, doc_count)
            )
            
            context = ""
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    source = results['metadatas'][0][i].get('source', 'Bilinmeyen')
                    employee = results['metadatas'][0][i].get('employee', 'Belirtilmemiş')
                    context += f"📌 [Kaynak: {source} | İlgili: {employee}]\n{doc}\n{'-'*30}\n"
                return context
            else:
                return "BİLGİ: Bu sorgu için veritabanında eşleşen veri bulunamadı."
        except Exception as e:
            logger.error(f"Sorgulama hatası: {e}")
            return f"HATA: Veritabanı sorgusu sırasında teknik bir sorun oluştu: {str(e)}"

    def get_evidence(self, query, top_k=6):
        """Sorguya en uygun kanıtları (structured) getirir."""
        if not self.collection:
            self.initialize()
            if not self.collection:
                return []

        doc_count = self.collection.count()
        if doc_count == 0:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, doc_count)
            )
            
            evidence = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    evidence.append({
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "score": results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0
                    })
            return evidence
        except Exception as e:
            logger.error(f"Kanıt toplama hatası: {e}")
            return []