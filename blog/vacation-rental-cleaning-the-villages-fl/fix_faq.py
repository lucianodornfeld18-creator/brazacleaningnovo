import re

filepath = r'C:\Users\lucia\Documents\brazacleaningnovo\blog\vacation-rental-cleaning-the-villages-fl\index.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# New FAQPage JSON-LD (8 questions, straight quotes, hyphens not em-dashes)
new_jsonld = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"How much does vacation rental turnover cleaning cost in The Villages, FL?","acceptedAnswer":{"@type":"Answer","text":"Vacation rental turnover cleaning in The Villages starts at $120-$130 for a 1-bedroom unit and ranges up to $155-$225 for a 4-bedroom home. Deep cleans after longer snowbird stays run 30-40% higher. Braza Cleaning provides free quotes with a 2-hour response - call or text (689) 242-7469."}},{"@type":"Question","name":"Do you offer same-day vacation rental cleaning in The Villages?","acceptedAnswer":{"@type":"Answer","text":"Yes - same-day turnover cleaning is available 7 days a week including weekends and holidays, subject to availability. Because peak snowbird season (November through April) fills fast, we recommend booking recurring slots in advance. Call or text (689) 242-7469 to check availability."}},{"@type":"Question","name":"What is included in a vacation rental turnover in The Villages?","acceptedAnswer":{"@type":"Answer","text":"Every turnover includes a full linen change and hotel-style bed making, bathroom scrubbing (toilet, shower, sink, mirrors), kitchen clean (countertops, stovetop, microwave interior, appliance exteriors), floor vacuuming and mopping, trash removal, damage check, and a WhatsApp photo report within 15 minutes of completion. Lanai and screened-porch cleaning is available as an add-on."}},{"@type":"Question","name":"Which neighborhoods and communities in The Villages area do you serve?","acceptedAnswer":{"@type":"Answer","text":"Braza Cleaning serves all of The Villages and the surrounding area, including Lady Lake, Leesburg, Summerfield, Oxford, and Wildwood. We are familiar with Villages HOA standards and community protocols for rental properties throughout the district."}},{"@type":"Question","name":"Do you bring your own cleaning supplies and products?","acceptedAnswer":{"@type":"Answer","text":"Yes - Braza Cleaning arrives fully equipped with all professional-grade cleaning products, microfiber cloths, and equipment. You do not need to provide anything. If your property has specific product preferences or sensitivities, let us know and we will accommodate them."}},{"@type":"Question","name":"Is Braza Cleaning licensed, insured, and background-checked in The Villages?","acceptedAnswer":{"@type":"Answer","text":"Yes - Braza Cleaning is fully licensed, bonded, and insured in Florida, and all team members pass background checks before entering client properties. Your vacation rental guests and your property are always protected."}},{"@type":"Question","name":"Do you require a contract for recurring vacation rental cleaning in The Villages?","acceptedAnswer":{"@type":"Answer","text":"No long-term contract is required. We work on a per-clean or recurring schedule basis, and you can adjust or cancel with reasonable notice. We back every clean with a satisfaction guarantee - if anything is missed, we return to fix it at no charge."}},{"@type":"Question","name":"How do I book vacation rental cleaning for my Villages property?","acceptedAnswer":{"@type":"Answer","text":"The easiest way is to message us on WhatsApp at wa.me/16892427469 or call and text (689) 242-7469. We respond within 2 hours and can schedule your first turnover quickly - even during peak snowbird season if slots are available."}}]}</script>'

new_faq_visible = (
    '<h2 style="font-size:1.35rem;font-weight:700;color:#1F2937;margin:2rem 0 1rem">Frequently Asked Questions</h2>\n'
    '<details style="border:0.5px solid #E5E7EB;border-radius:8px;padding:.875rem 1rem;margin-bottom:.5rem"><summary style="font-weight:600;cursor:pointer">How much does vacation rental turnover cleaning cost in The Villages, FL?</summary><p style="margin:.75rem 0 0;color:#4B5563;line-height:1.7">Vacation rental turnover cleaning in The Villages starts at $120-$130 for a 1-bedroom unit and ranges up to $155-$225 for a 4-bedroom home. Deep cleans after longer snowbird stays run 30-40% higher. Braza Cleaning provides free quotes with a 2-hour response - call or text (689) 242-7469.</p></details>\n'
    '<details style="border:0.5px solid #E5E7EB;border-radius:8px;padding:.875rem 1rem;margin-bottom:.5rem"><summary style="font-weight:600;cursor:pointer">Do you offer same-day vacation rental cleaning in The Villages?</summary><p style="margin:.75rem 0 0;color:#4B5563;line-height:1.7">Yes - same-day turnover cleaning is available 7 days a week including weekends and holidays, subject to availability. Because peak snowbird season (November through April) fills fast, we recommend booking recurring slots in advance. Call or text (689) 242-7469 to check availability.</p></details>\n'
    '<details style="border:0.5px solid #E5E7EB;border-radius:8px;padding:.875rem 1rem;margin-bottom:.5rem"><summary style="font-weight:600;cursor:pointer">What is included in a vacation rental turnover in The Villages?</summary><p style="margin:.75rem 0 0;color:#4B5563;line-height:1.7">Every turnover includes a full linen change and hotel-style bed making, bathroom scrubbing (toilet, shower, sink, mirrors), kitchen clean (countertops, stovetop, microwave interior, appliance exteriors), floor vacuuming and mopping, trash removal, damage check, and a WhatsApp photo report within 15 minutes of completion. Lanai and screened-porch cleaning is available as an add-on.</p></details>\n'
    '<details style="border:0.5px solid #E5E7EB;border-radius:8px;padding:.875rem 1rem;margin-bottom:.5rem"><summary style="font-weight:600;cursor:pointer">Which neighborhoods and communities in The Villages area do you serve?</summary><p style="margin:.75rem 0 0;color:#4B5563;line-height:1.7">Braza Cleaning serves all of The Villages and the surrounding area, including Lady Lake, Leesburg, Summerfield, Oxford, and Wildwood. We are familiar with Villages HOA standards and community protocols for rental properties throughout the district.</p></details>\n'
    '<details style="border:0.5px solid #E5E7EB;border-radius:8px;padding:.875rem 1rem;margin-bottom:.5rem"><summary style="font-weight:600;cursor:pointer">Do you bring your own cleaning supplies and products?</summary><p style="margin:.75rem 0 0;color:#4B5563;line-height:1.7">Yes - Braza Cleaning arrives fully equipped with all professional-grade cleaning products, microfiber cloths, and equipment. You do not need to provide anything. If your property has specific product preferences or sensitivities, let us know and we will accommodate them.</p></details>\n'
    '<details style="border:0.5px solid #E5E7EB;border-radius:8px;padding:.875rem 1rem;margin-bottom:.5rem"><summary style="font-weight:600;cursor:pointer">Is Braza Cleaning licensed, insured, and background-checked in The Villages?</summary><p style="margin:.75rem 0 0;color:#4B5563;line-height:1.7">Yes - Braza Cleaning is fully licensed, bonded, and insured in Florida, and all team members pass background checks before entering client properties. Your vacation rental guests and your property are always protected.</p></details>\n'
    '<details style="border:0.5px solid #E5E7EB;border-radius:8px;padding:.875rem 1rem;margin-bottom:.5rem"><summary style="font-weight:600;cursor:pointer">Do you require a contract for recurring vacation rental cleaning in The Villages?</summary><p style="margin:.75rem 0 0;color:#4B5563;line-height:1.7">No long-term contract is required. We work on a per-clean or recurring schedule basis, and you can adjust or cancel with reasonable notice. We back every clean with a satisfaction guarantee - if anything is missed, we return to fix it at no charge.</p></details>\n'
    '<details style="border:0.5px solid #E5E7EB;border-radius:8px;padding:.875rem 1rem;margin-bottom:.5rem"><summary style="font-weight:600;cursor:pointer">How do I book vacation rental cleaning for my Villages property?</summary><p style="margin:.75rem 0 0;color:#4B5563;line-height:1.7">The easiest way is to message us on WhatsApp at wa.me/16892427469 or call and text (689) 242-7469. We respond within 2 hours and can schedule your first turnover quickly - even during peak snowbird season if slots are available.</p></details>'
)

# Pattern: FAQPage JSON-LD script tag, then h2, then all details blocks (up to blank line before next div)
pattern = re.compile(
    r'<script type="application/ld\+json">\{"@context": "https://schema\.org", "@type": "FAQPage".*?</script>'
    r'<h2 style="font-size:1\.35rem;font-weight:700;color:#1F2937;margin:2rem 0 1rem">Frequently Asked Questions</h2>\n'
    r'(?:<details[^>]*>.*?</details>\n?)+',
    re.DOTALL
)

replacement = new_jsonld + '\n' + new_faq_visible + '\n'

new_content, count = re.subn(pattern, replacement, content)

if count == 0:
    print("ERROR: pattern not matched")
    # Debug: show what the FAQPage script looks like
    idx = content.find('"@type": "FAQPage"')
    if idx >= 0:
        print("Found FAQPage at index", idx)
        print(repr(content[idx-50:idx+200]))
    else:
        print("FAQPage not found in content at all")
else:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: replaced", count, "occurrence(s)")
    details_count = new_content.count('<details style="border:0.5px solid #E5E7EB')
    schema_q_count = new_content.count('"@type":"Question"')
    print("Visible <details> count:", details_count)
    print("Schema Question count:", schema_q_count)
