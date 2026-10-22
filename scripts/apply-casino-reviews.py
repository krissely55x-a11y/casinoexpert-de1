import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PAGES_ROOT = ROOT / "src" / "pages" / "casinos"
SOURCE = (ROOT / "scripts" / "add-casino-reviews.mjs").read_text(encoding="utf-8")


def load_reviews():
    data = SOURCE.split("const reviewsByCasino = {", 1)[1].split("\n};", 1)[0]
    casinos = {}
    entry_pattern = re.compile(r'  (?:"([^"]+)"|([a-z]+)): \[\n(.*?)\n  \],', re.S)
    review_pattern = re.compile(
        r'    \["(.*?)", ([1-5]), "(.*?)", "(.*?)", "(.*?)"\],'
    )
    for match in entry_pattern.finditer(data):
        slug = match.group(1) or match.group(2)
        casinos[slug] = [
            (title, int(rating), date, content, author)
            for title, rating, date, content, author in review_pattern.findall(match.group(3))
        ]
    return casinos


LABELS = {
    5: "Perfekt",
    4: "Sehr gut",
    3: "Durchschnitt",
    2: "Schlecht",
    1: "Furchtbar",
}


def stars(rating):
    return "".join(
        f'<span class="glsr-star glsr-star-{"full" if index < rating else "empty"}" aria-hidden="true"></span>'
        for index in range(5)
    )


def render_review(slug, assigned_post, review, index):
    title, rating, date, content, author = review
    return f"""<div class="glsr-review" data-type="local" data-source="oce-2026-batch" id="review-oce-{slug}-{index + 1}" data-assigned='{{"assigned_posts":[{assigned_post}]}}'>
    <div class="glsr-review-title"><h4 class="glsr-tag-value">{title}</h4></div>
    <div class="glsr-review-rating"><div class="glsr-star-rating glsr-stars" role="img" aria-label="Rated {rating} out of 5 stars" data-rating="{rating}" data-reviews="0">{stars(rating)}</div></div> <div class="glsr-review-date"><span class="glsr-tag-value">{date}</span></div>
    <div class="glsr-review-content"><div class="glsr-tag-value" data-expanded="false"><p>{content}</p></div></div>
    <div class="glsr-review-author"><span class="glsr-tag-value">{author}</span></div>
</div>"""


def update_summary(segment, ratings):
    count = len(ratings)
    average = sum(ratings) / count
    average_text = f"{average:.1f}".replace(".", ",")
    display_stars = int(average + 0.5)

    segment = re.sub(
        r'(<div class="glsr-summary-rating"><span class="glsr-tag-value">)[^<]+',
        rf"\g<1>{average_text}",
        segment,
        count=1,
    )
    segment = re.sub(
        r'<div class="glsr-summary-stars"><div class="glsr-star-rating glsr-stars"[\s\S]*?</div></div>',
        f'<div class="glsr-summary-stars"><div class="glsr-star-rating glsr-stars" role="img" aria-label="Rated {average_text} out of 5 stars based on {count} ratings" data-rating="{average_text}" data-reviews="{count}">{stars(display_stars)}</div></div>',
        segment,
        count=1,
    )
    noun = "Bewertung" if count == 1 else "Bewertungen"
    segment = re.sub(
        r'(<div class="glsr-summary-text"><span class="glsr-tag-value">)[^<]+',
        rf"\g<1>{average_text} von 5 Sternen (basierend auf {count} {noun})",
        segment,
        count=1,
    )

    for rating in range(1, 6):
        percentage = round(ratings.count(rating) / count * 100)
        pattern = re.compile(
            rf'(<div class="glsr-bar" data-level=["\']{rating}["\']><span class="glsr-bar-label">{LABELS[rating]}</span><span class="glsr-bar-background"><span class="glsr-bar-background-percent" style="width:)[^%]+(%"></span></span><span class="glsr-bar-percent">)[^<]+'
        )
        segment = pattern.sub(
            rf"\g<1>{percentage}\g<2>{percentage}%",
            segment,
            count=1,
        )
    return segment


def main():
    reviews_by_casino = load_reviews()
    if len(reviews_by_casino) != 19:
        raise RuntimeError(f"Expected 19 casino entries, found {len(reviews_by_casino)}")

    for slug, new_reviews in reviews_by_casino.items():
        filename = PAGES_ROOT / slug / "_body.html"
        html = filename.read_text(encoding="utf-8")

        if f'id="review-oce-{slug}-1"' in html:
            print(f"{slug}: already updated")
            continue

        summary_match = re.search(
            r'<div class="glsr glsr-default"[^>]+data-shortcode=["\']site_reviews_summary["\']',
            html,
        )
        form_match = re.search(
            r'<div class="glsr glsr-default"[^>]+data-shortcode=["\']site_reviews_form["\']',
            html,
        )
        if not summary_match or not form_match or form_match.start() <= summary_match.start():
            raise RuntimeError(f"{slug}: review summary or form not found")

        summary_start = summary_match.start()
        form_start = form_match.start()
        summary_segment = html[summary_start:form_start]
        assigned_match = re.search(r'data-assigned_posts=["\'](\d+)["\']', summary_segment)
        if not assigned_match:
            raise RuntimeError(f"{slug}: assigned post ID not found")
        assigned_post = assigned_match.group(1)

        reviews_match = re.search(
            r'<div class="glsr glsr-default"[^>]+data-shortcode=["\']site_reviews["\']',
            html,
        )
        if not reviews_match:
            raise RuntimeError(f"{slug}: reviews list not found")
        reviews_start = reviews_match.start()
        next_heading = html.find("<h2", reviews_start)
        reviews_end = next_heading if next_heading >= 0 else len(html)
        reviews_segment = html[reviews_start:reviews_end]
        existing_ratings = [
            int(value)
            for value in re.findall(
                r'<div class="glsr-review"[\s\S]*?data-rating=["\']([1-5])(?:,0)?["\']',
                reviews_segment,
            )
        ]
        all_ratings = existing_ratings + [review[1] for review in new_reviews]

        updated_summary = update_summary(summary_segment, all_ratings)
        html = html[:summary_start] + updated_summary + html[form_start:]

        reviews_match = re.search(
            r'<div class="glsr glsr-default"[^>]+data-shortcode=["\']site_reviews["\']',
            html,
        )
        list_start = html.find('<div class="glsr-reviews">', reviews_match.start())
        if list_start < 0:
            raise RuntimeError(f"{slug}: reviews container not found")
        insertion_point = list_start + len('<div class="glsr-reviews">')
        cards = "\n".join(
            render_review(slug, assigned_post, review, index)
            for index, review in enumerate(new_reviews)
        )
        tail = re.sub(
            r'^\s*<p class="glsr-no-margins">Es gibt noch keine Kundenbewertungen\.</p>',
            "",
            html[insertion_point:],
            count=1,
        )
        html = html[:insertion_point] + f"\n{cards}\n" + tail

        filename.write_text(html, encoding="utf-8", newline="")
        print(f"{slug}: added {len(new_reviews)} reviews")

    generated_total = 0
    for slug, expected_reviews in reviews_by_casino.items():
        html = (PAGES_ROOT / slug / "_body.html").read_text(encoding="utf-8")
        generated_count = html.count('data-source="oce-2026-batch"')
        if generated_count != len(expected_reviews):
            raise RuntimeError(
                f"{slug}: expected {len(expected_reviews)} generated reviews, found {generated_count}"
            )
        generated_total += generated_count

        reviews_match = re.search(
            r'<div class="glsr glsr-default"[^>]+data-shortcode=["\']site_reviews["\']',
            html,
        )
        next_heading = html.find("<h2", reviews_match.start())
        reviews_segment = html[reviews_match.start():next_heading]
        total_reviews = len(re.findall(r'<div class="glsr-review" ', reviews_segment))

        summary_match = re.search(
            r'data-shortcode=["\']site_reviews_summary["\'][\s\S]*?data-reviews=["\'](\d+)["\']',
            html,
        )
        if not summary_match or int(summary_match.group(1)) != total_reviews:
            shown = summary_match.group(1) if summary_match else "missing"
            raise RuntimeError(
                f"{slug}: summary shows {shown} reviews, list contains {total_reviews}"
            )
        if "Es gibt noch keine Kundenbewertungen." in reviews_segment:
            raise RuntimeError(f"{slug}: stale empty-review message remains")

    print(f"validated: {generated_total} new reviews across {len(reviews_by_casino)} casino pages")


if __name__ == "__main__":
    main()
