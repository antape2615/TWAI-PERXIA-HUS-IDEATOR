import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service to manage and query historical HUs as knowledge base"""
    
    def __init__(self, storage_path: str = "data/knowledge_base"):
        self.storage_path = storage_path
        self.hu_index_file = os.path.join(storage_path, "hu_index.json")
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Ensure storage directory and index file exist"""
        os.makedirs(self.storage_path, exist_ok=True)
        if not os.path.exists(self.hu_index_file):
            self._save_index([])
    
    def _load_index(self) -> List[Dict]:
        """Load HU index from file"""
        try:
            with open(self.hu_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading HU index: {e}")
            return []
    
    def _save_index(self, index: List[Dict]):
        """Save HU index to file"""
        try:
            with open(self.hu_index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving HU index: {e}")
    
    def add_hu(
        self,
        hu_id: str,
        title: str,
        content: str,
        requirement: str,
        tags: Optional[List[str]] = None,
        work_item_id: Optional[int] = None,
        work_item_url: Optional[str] = None
    ) -> str:
        """Add a new HU to the knowledge base"""
        
        # Extract keywords from title and requirement
        keywords = self._extract_keywords(title + " " + requirement)
        
        hu_entry = {
            "hu_id": hu_id,
            "title": title,
            "requirement": requirement,
            "keywords": keywords,
            "tags": tags or [],
            "work_item_id": work_item_id,
            "work_item_url": work_item_url,
            "created_at": datetime.now().isoformat(),
            "content_file": f"{hu_id}.json"
        }
        
        # Save full HU content to separate file
        content_path = os.path.join(self.storage_path, f"{hu_id}.json")
        try:
            with open(content_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "hu_id": hu_id,
                    "title": title,
                    "content": content,
                    "requirement": requirement,
                    "created_at": hu_entry["created_at"]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving HU content: {e}")
            raise
        
        # Add to index
        index = self._load_index()
        index.append(hu_entry)
        self._save_index(index)
        
        logger.info(f"Added HU {hu_id} to knowledge base with {len(keywords)} keywords")
        return hu_id
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        # Common words to ignore
        stop_words = {
            'el', 'la', 'de', 'en', 'y', 'a', 'los', 'las', 'del', 'un', 'una',
            'por', 'para', 'con', 'que', 'se', 'al', 'es', 'su', 'como', 'o',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
        }
        
        # Clean and split text
        words = text.lower().replace(',', ' ').replace('.', ' ').split()
        
        # Filter keywords (length > 3, not stop words)
        keywords = [
            word for word in words 
            if len(word) > 3 and word not in stop_words
        ]
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def search_related_hus(
        self,
        requirement: str,
        min_relevance: float = 0.3,
        max_results: int = 5
    ) -> List[Dict]:
        """Search for HUs related to a requirement"""
        
        # Extract keywords from requirement
        req_keywords = set(self._extract_keywords(requirement))
        
        if not req_keywords:
            return []
        
        # Load index
        index = self._load_index()
        
        # Calculate relevance scores
        results = []
        for hu_entry in index:
            hu_keywords = set(hu_entry.get("keywords", []))
            
            # Calculate keyword overlap
            common_keywords = req_keywords.intersection(hu_keywords)
            if not common_keywords:
                continue
            
            # Relevance score: Jaccard similarity
            relevance = len(common_keywords) / len(req_keywords.union(hu_keywords))
            
            if relevance >= min_relevance:
                results.append({
                    "hu_id": hu_entry["hu_id"],
                    "title": hu_entry["title"],
                    "requirement": hu_entry["requirement"],
                    "work_item_id": hu_entry.get("work_item_id"),
                    "work_item_url": hu_entry.get("work_item_url"),
                    "relevance": relevance,
                    "common_keywords": list(common_keywords)
                })
        
        # Sort by relevance and return top results
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:max_results]
    
    def get_hu_content(self, hu_id: str) -> Optional[Dict]:
        """Get full content of a specific HU"""
        content_path = os.path.join(self.storage_path, f"{hu_id}.json")
        
        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"HU content not found: {hu_id}")
            return None
        except Exception as e:
            logger.error(f"Error loading HU content: {e}")
            return None
    
    def get_all_hus(self) -> List[Dict]:
        """Get list of all HUs in knowledge base"""
        return self._load_index()
    
    def get_statistics(self) -> Dict:
        """Get statistics about the knowledge base"""
        index = self._load_index()
        
        all_keywords = []
        all_tags = []
        
        for hu in index:
            all_keywords.extend(hu.get("keywords", []))
            all_tags.extend(hu.get("tags", []))
        
        # Count keyword frequency
        keyword_freq = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Get top keywords
        top_keywords = sorted(
            keyword_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]
        
        return {
            "total_hus": len(index),
            "total_keywords": len(set(all_keywords)),
            "total_tags": len(set(all_tags)),
            "top_keywords": [{"keyword": k, "count": c} for k, c in top_keywords],
            "most_recent": index[-1] if index else None
        }



