from src.embeddings import _dedup_by_item_id, _data_fingerprint
from src.rag import language_ok, match_virtual_tours


# ---------- _dedup_by_item_id ----------

def test_dedup_removes_duplicate_item_ids():
    data = [
        {"item_id": "Q1", "label": "A"},
        {"item_id": "Q2", "label": "B"},
        {"item_id": "Q1", "label": "A (نسخة مكررة)"},
    ]
    result = _dedup_by_item_id(data)
    assert len(result) == 2
    assert [item["item_id"] for item in result] == ["Q1", "Q2"]


def test_dedup_keeps_first_occurrence():
    """
    لو نفس الـ item_id اتكرر، لازم نحتفظ بأول نسخة ظهرت (زي سلوك دمج المتاحف
    اللي اكتشفنا فيه إن أول نسخة كانت أحيانًا بتاخد الأولوية غلط)، عشان أي حد
    يقرا الكود يبقى واضح ومتوقع مين اللي بيتحفظ.
    """
    data = [
        {"item_id": "Q1", "label": "النسخة الأولى"},
        {"item_id": "Q1", "label": "النسخة التانية"},
    ]
    result = _dedup_by_item_id(data)
    assert len(result) == 1
    assert result[0]["label"] == "النسخة الأولى"


def test_dedup_empty_list():
    assert _dedup_by_item_id([]) == []


# ---------- _data_fingerprint ----------

def test_fingerprint_same_data_same_hash():
    data = [{"item_id": "Q1", "document_text": "hello"}]
    assert _data_fingerprint(data) == _data_fingerprint(data)


def test_fingerprint_changes_when_content_changes_but_count_stays_same():
    """
    هذا هو البَگ اللي كنا بنصلحه في نقطة #5: تعديل محتوى قطعة موجودة
    (بدون تغيير العدد الكلي) لازم يغيّر الـ fingerprint.
    """
    before = [{"item_id": "Q1", "document_text": "Material: خشب"}]
    after = [{"item_id": "Q1", "document_text": "Material: ذهب"}]
    assert _data_fingerprint(before) != _data_fingerprint(after)


def test_fingerprint_same_when_nothing_changed():
    a = [{"item_id": "Q1", "document_text": "hello"}, {"item_id": "Q2", "document_text": "world"}]
    b = [{"item_id": "Q1", "document_text": "hello"}, {"item_id": "Q2", "document_text": "world"}]
    assert _data_fingerprint(a) == _data_fingerprint(b)


# ---------- language_ok ----------

def test_language_ok_arabic_text_passes():
    assert language_ok("هذه قطعة أثرية مصرية قديمة وجميلة جداً", "arabic") is True


def test_language_ok_english_text_fails_arabic_requirement():
    assert language_ok("This is an ancient Egyptian artifact", "arabic") is False


def test_language_ok_english_requirement_always_passes():
    # الفحص بتاعنا بيراقب العربي بس، أي حاجة تانية بتعدي زي ما هي
    assert language_ok("Any text at all", "english") is True


def test_language_ok_short_text_is_ignored():
    # نص قصير جداً (أقل من 8 حروف) معندناش معلومات كفاية نحكم عليه
    assert language_ok("hi", "arabic") is True


# ---------- match_virtual_tours ----------

def test_match_virtual_tours_no_match_returns_empty():
    assert match_virtual_tours("سؤال عشوائي مالوش علاقة", []) == []


def test_match_virtual_tours_returns_max_two():
    """
    match_virtual_tours بتعتمد على data/virtual_tours.json الفعلي، فبنتأكد بس إن
    القاعدة العامة (أقصى حاجة قطعتين) بتتحترم مهما كان عدد القطع المسترجعة.
    """
    sources = [{"label": "أي قطعة", "museum": "Egyptian Museum, Cairo"}]
    result = match_virtual_tours("جولة افتراضية", sources)
    assert len(result) <= 2
