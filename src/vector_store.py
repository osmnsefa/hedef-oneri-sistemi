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
            
            ids = [f"doc_{i}" for i in range(len(chunked_docs))]
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

    def get_context(self, query, top_k=4):
        """Sorguya en uygun bağlamı getirir."""
        if not self.collection:
            return "Vektör veritabanı başlatılamadı (Eksik kütüphane veya bağlantı sorunu)."

        if self.collection.count() == 0:
            return "Veri tabanında hiç bilgi yok."

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        context = ""
        # Results yapısı: {'ids': [['id1', ...]], 'documents': [['text1', ...]], ...}
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                source = results['metadatas'][0][i].get('source', 'Bilinmeyen')
                context += f"📌 [Kaynak: {source}]\n{doc}\n{'-'*30}\n"
        
        return context