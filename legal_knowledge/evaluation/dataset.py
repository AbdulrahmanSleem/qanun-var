"""
Golden Benchmark Evaluation Dataset for Egyptian Legal Retrieval & Q&A.
Manually curated from authentic legislation (Civil Code, Labor Law, Commercial Code).
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class LegalEvaluationItem(BaseModel):
    query_id: str
    question: str
    expected_law_number: Optional[str]
    expected_law_name: str
    expected_article_number: Optional[str]
    is_out_of_domain: bool = False  # Should trigger abstention
    ground_truth_summary: str


BENCHMARK_DATASET: List[LegalEvaluationItem] = [
    LegalEvaluationItem(
        query_id="Q1_LABOR_PROBATION",
        question="ما هي أقصى مدة مسموح بها قانوناً لفترة الاختبار في عقد العمل في مصر وهل يجوز تكرارها؟",
        expected_law_number="12",
        expected_law_name="قانون العمل",
        expected_article_number="31",
        is_out_of_domain=False,
        ground_truth_summary="لا يجوز تحديد مدة الاختبار بأكثر من ثلاثة أشهر، ولا يجوز تعيين العامل تحت الاختبار أكثر من مرة واحدة عند صاحب عمل واحد وفقاً للمادة 31 من قانون العمل."
    ),
    LegalEvaluationItem(
        query_id="Q2_CIVIL_SANCTITY_CONTRACT",
        question="هل يجوز نقض أو تعديل العقد بإرادة منفردة وما أثر الظروف الطارئة المرهقة للمدين؟",
        expected_law_number="131",
        expected_law_name="القانون المدني",
        expected_article_number="147",
        is_out_of_domain=False,
        ground_truth_summary="العقد شريعة المتعاقدين فلا يجوز نقضه أو تعديله إلا باتفاق الطرفين، ويجوز للقاضي في الحوادث الاستثنائية رد الالتزام المرهق للحد المعقول وفق المادة 147 من القانون المدني."
    ),
    LegalEvaluationItem(
        query_id="Q3_COMMERCIAL_CHECK_DUE",
        question="ما هو ميعاد استحقاق الشيك وهل يعتد بالاتفاق على تأجيل صرفه في قانون التجارة المصري؟",
        expected_law_number="17",
        expected_law_name="قانون التجارة",
        expected_article_number="537",
        is_out_of_domain=False,
        ground_truth_summary="يعتبر الشيك مستحق الوفاء بمجرد الاطلاع عليه، وكل بيان يخالف ذلك يعتبر كأن لم يكن طبقاً للمادة 537 من قانون التجارة."
    ),
    LegalEvaluationItem(
        query_id="Q4_LABOR_TERMINATION_ABSENCE",
        question="كم يوماً يجب أن يتغيبها العامل بدون إذن حتى يجوز لصاحب العمل فصله بسبب الغياب؟",
        expected_law_number="12",
        expected_law_name="قانون العمل",
        expected_article_number="69",
        is_out_of_domain=False,
        ground_truth_summary="يجوز فصل العامل إذا غاب بدون عذر مشروع أكثر من عشرين يوماً متقطعة خلال السنة أو أكثر من عشرة أيام متتالية وفق المادة 69 من قانون العمل."
    ),
    LegalEvaluationItem(
        query_id="Q5_CIVIL_TORT_LIABILITY",
        question="ما هي القاعدة العامة في التعويض عن المسؤولية التقصيرية والخطأ المسبب لضرر؟",
        expected_law_number="131",
        expected_law_name="القانون المدني",
        expected_article_number="163",
        is_out_of_domain=False,
        ground_truth_summary="كل خطأ سبب ضرراً للغير يلزم من ارتكبه بالتعويض وفق المادة 163 من القانون المدني المصري."
    ),
    LegalEvaluationItem(
        query_id="Q6_NEGATIVE_TRAFFIC_OUT_OF_SCOPE",
        question="ما هي عقوبة السير بدون رخصة قيادة أو تجاوز السرعة المقررة في قانون المرور؟",
        expected_law_number=None,
        expected_law_name="قانون المرور",
        expected_article_number=None,
        is_out_of_domain=True,
        ground_truth_summary="خارج نطاق قاعدة المعرفة المتاحة حالياً ويجب على النظام الامتناع عن الإفتاء لعدم وجود نصوص داعمة."
    ),
]
