from dataclasses import asdict
from sqlalchemy.sql.functions import func

def addFAQStats(faqs, total_num_queries, unidentified_queries=None):
    updated_faqs = []
    
    for f in faqs:
        new_faq = asdict(f)
        num_queries = len(f.queries) 
        num_resolved = len(list(filter(lambda x: x.resolved == True, f.queries)))
        hit_rate = round((num_queries / total_num_queries)*100) if total_num_queries > 0 else 0
        success_rate = round((num_resolved / num_queries)*100) if num_queries > 0 else 0
        new_faq['hit_rate'] = hit_rate
        new_faq['success_rate'] = success_rate
        new_faq['queries'] = num_queries
        new_faq['resolved']  = num_resolved
        updated_faqs.append(formatFAQ(new_faq))

    if unidentified_queries:
        num_unidentified = len(unidentified_queries)
        num_resolved_unidentified =len(list(filter(lambda x: x.resolved ==True, unidentified_queries )))
        hit_rate = round((num_unidentified/total_num_queries)* 100) if total_num_queries > 0 else 0
        success_rate = round((num_resolved_unidentified/num_unidentified)*100) if num_unidentified >0 else 0
        other = {"tag": "Other", "responses": [], "patterns":[], "queries":num_unidentified, "resolved":num_resolved_unidentified, "hit_rate": hit_rate, "success_rate":success_rate}
        updated_faqs.append(other)
    return updated_faqs

def getCount(q):
    count_q = q.statement.with_only_columns(func.count()).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count

def formatFAQ(faq):
    faq['patterns'] = faq['patterns'].split('|')
    faq['responses'] = faq['responses'].split('|')
    return faq
