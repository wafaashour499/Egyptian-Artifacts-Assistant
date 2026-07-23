"""
إعدادات مشتركة للاختبارات.

المكتبتين sentence_transformers و chromadb تقيلتين (بتنزل موديل / بتحتاج قرص) ومش
لازمين فعليًا عشان نختبر منطق البيانات البحت (dedup, fingerprint, language check,
virtual tours matching). فبنعمل لهم "stub" بسيط هنا قبل أي import لـ src.embeddings،
عشان الاختبارات تشتغل بسرعة ومن غير إنترنت.
"""
import os
import sys
import types
from unittest.mock import MagicMock

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

if "sentence_transformers" not in sys.modules:
    stub = types.ModuleType("sentence_transformers")
    stub.SentenceTransformer = MagicMock()
    sys.modules["sentence_transformers"] = stub

if "chromadb" not in sys.modules:
    sys.modules["chromadb"] = MagicMock()
