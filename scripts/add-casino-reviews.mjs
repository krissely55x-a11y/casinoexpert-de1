import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pagesRoot = path.join(root, "src", "pages", "casinos");

const reviewsByCasino = {
  vinyl: [
    ["Auszahlung kam an", 4, "19/10/2026", "Hab Vinyl Casino erst wegen der vielen Slots getestet. Auszahlung auf Krypto war nach knapp nem Tag da also von mir 4 Sterne", "Micha"],
    ["bonus ok aber genau lesen", 4, "07/09/2026", "Meine Vinyl Casino Erfahrungen sind bisher gut. Bonus hat funktioniert nur die Umsatzbedingungen sollte man vorher lesen dann gibts auch kein Theater", "timo82"],
  ],
  vegaz: [
    ["ohne limit nervt nix", 5, "11/10/2026", "Vegaz Casino ohne deutsche Lizenz war genau was ich gesucht hab. Keine 1 Euro Grenze und die Seite läuft aufm Handy sauber", "Chris B"],
    ["cashout war fix", 4, "28/08/2026", "Bei meiner Vegaz Casino Auszahlung musste ich einmal den Ausweis schicken danach war das Geld am nächsten Abend drauf. passt", "Sven"],
    ["viele slots", 4, "03/07/2026", "Vegaz Casino Erfahrungen nach 2 Monaten: gute Slot Auswahl und Login klappt immer. Support auf deutsch könnte schneller sein", "andi_77"],
  ],
  "rockwin-io": [
    ["krypto einzahlen klappt", 4, "15/09/2026", "Rockwin Casino mit Krypto getestet Einzahlung war nach paar Minuten drauf. Auszahlung dauerte länger aber kam ohne nachfragen", "Deniz"],
  ],
  rebellion: [
    ["bonus code ging direkt", 5, "02/10/2026", "Rebellion Casino Bonus Code bei der Anmeldung eingetragen und die Freispiele waren sofort da. so muss das", "Lukas"],
    ["auszahlung 2 tage", 4, "21/09/2026", "Meine Rebellion Casino Auszahlung hat 2 Tage gebraucht. Nicht mega schnell aber auch kein Stress mit dem Support", "Jens K."],
    ["läuft gut am handy", 5, "30/08/2026", "Rebellion Casino App gibts zwar nicht extra aber im Browser läuft alles flüssig auch Pragmatic Games", "melli"],
    ["bedingungen bisschen viel", 3, "12/06/2026", "Rebellion Casino Erfahrungen gemischt. Spiele und Bonus gut aber bei den Bonusbedingungen hab ich erstmal dreimal lesen müssen", "Fabi"],
  ],
  rant: [
    ["endlich normale einsätze", 5, "17/10/2026", "Rant Casino ohne deutsche Lizenz getestet weil mich das 1 Euro Limit nervt. Registrierung kurz und Slots laden schnell", "Nico91"],
    ["support war echt da", 4, "25/08/2026", "Beim Rant Casino Login hing die Bestätigungsmail. Chat angeschrieben und nach 10 min wars gelöst also alles gut", "Kai"],
  ],
  myempire: [
    ["mal was anderes", 5, "06/10/2026", "MyEmpire Casino Erfahrungen bisher top. Das City Ding ist tatsächlich ganz witzig und nicht nur Deko", "Sarah"],
    ["auszahlen ging", 4, "18/09/2026", "MyEmpire Casino Auszahlung auf Mastercard hat bei mir 3 Werktage gedauert. Verifizierung ging dafür schnell", "Paule"],
    ["bonus nicht schlecht", 4, "29/07/2026", "Den MyEmpire Casino Bonus hab ich komplett umgesetzt bekommen. Man muss halt auf die erlaubten Slots achten sonst zählt nix", "Marvin"],
  ],
  levelup: [
    ["free spins bekommen", 5, "13/10/2026", "LevelUp Casino Bonus ohne Einzahlung benutzt und die Freispiele kamen direkt nachm Login. Gewinn war klein aber gratis ist gratis", "Nadine"],
    ["schneller cashout", 5, "01/10/2026", "LevelUp Casino Auszahlung mit Litecoin in ca 6 Stunden. Hatte vorher schon verifiziert vielleicht gings deshalb so fix", "robert86"],
    ["app läuft sauber", 4, "22/08/2026", "LevelUp Casino App auf Android läuft bei mir ohne Abstürze. Nur die Spielsuche könnte besser sein", "Ben"],
    ["zu viele bonus regeln", 3, "09/05/2026", "LevelUp Casino Erfahrungen an sich ok aber der Bonus war mir zu kompliziert. Spiele ohne Bonus machen mehr Spaß", "Doro"],
  ],
  kryptosino: [
    ["btc war schnell drauf", 5, "09/10/2026", "Kryptosino Casino Einzahlung mit BTC ging in unter 10 min. Genau deshalb spiel ich lieber im Krypto Casino", "JanX"],
    ["deutsch wäre besser", 3, "14/08/2026", "Meine Kryptosino Erfahrungen sind ok nur paar Menüs bleiben englisch. Auszahlung kam trotzdem und das ist am Ende wichtiger", "Ralf"],
  ],
  horus: [
    ["bonus ohne umsatz nice", 5, "20/10/2026", "Horus Casino Bonus ohne Umsatz fand ich stark. Hab 60 Euro gewonnen und direkt auszahlen können ohne ewig zu drehen", "Leo"],
    ["verifizierung ging fix", 4, "04/09/2026", "Für die Horus Casino Auszahlung wollten sie Ausweis und Adressnachweis. Nach Freigabe war das Geld einen Tag später da", "Steffi"],
    ["mobil ganz ordentlich", 4, "27/07/2026", "Horus Casino App im Browser reicht völlig. Book of Dead läuft flüssig nur der Login lädt manchmal bisschen lang", "Olli"],
  ],
  hejgo: [
    ["gute pragmatic auswahl", 5, "16/10/2026", "Hejgo Casino hat echt viele Pragmatic Slots. Sweet Bonanza läuft ohne ruckeln auch wenn ich nur mobiles Netz hab", "Emre"],
    ["auszahlung angekommen", 4, "05/10/2026", "Hejgo Casino Auszahlung Freitag beantragt und Montag aufm Konto. Wochenende zählt wohl nicht also passt schon", "Tobi"],
    ["bonus war direkt aktiv", 5, "02/09/2026", "Beim Hejgo Casino Bonus musste ich keinen Code suchen. eingezahlt und Freispiele waren da easy", "Laura K"],
    ["chat könnte schneller", 3, "19/06/2026", "Hejgo Casino Erfahrungen soweit okay. Beim Login Problem hing ich aber fast 20 min im Chat darum nur 3 Sterne", "Holger"],
  ],
  goodman: [
    ["macht was es soll", 4, "18/10/2026", "Goodman Casino Erfahrungen nach paar Wochen: ordentlich Spiele Login problemlos und bisher keine komischen Sachen", "M. Schulz"],
    ["cashout ohne drama", 5, "23/09/2026", "Goodman Casino Auszahlung über Skrill war am selben Abend da. Hatte 120 Euro und alles komplett bekommen", "jana"],
  ],
  crownplay: [
    ["live casino gefällt", 5, "08/10/2026", "CrownPlay Casino hat gute Live Tische und nicht diese niedrigen Limits. Dealer laden bei mir auch mobil schnell", "Alex P"],
    ["bonusbedingungen beachten", 4, "11/09/2026", "CrownPlay Casino Bonus ist okay aber max bet nicht übersehen. Hab mich dran gehalten und Auszahlung ging durch", "Dennis"],
    ["verifizierung dauert", 3, "03/08/2026", "Meine CrownPlay Casino Erfahrungen waren erst nervig wegen KYC. Hat 2 Tage gedauert danach lief die Auszahlung normal", "Karo"],
  ],
  casinobuck: [
    ["solides casino", 4, "26/09/2026", "CasinoBuck Erfahrungen bisher solide. Viele neue Slots und die erste Auszahlung per Bank war nach 2 Tagen da", "Matze"],
  ],
  gslot: [
    ["bonus code klappt", 5, "14/10/2026", "GSlot Casino Bonus Code eingegeben und 20 Freispiele ohne Einzahlung bekommen. Ging wirklich ohne Karte oder so", "Flo"],
    ["krypto cashout top", 5, "29/09/2026", "GSlot Casino Auszahlung mit USDT war nach 4 Stunden erledigt. Für mich bisher der schnellste Cashout", "Viktor"],
    ["app brauch ich nicht", 4, "10/08/2026", "GSlot Casino App hab ich nicht gefunden aber mobil im Chrome läufts eh gut. Slots öffnen schnell", "Sascha"],
    ["bonus eher mittel", 3, "24/05/2026", "GSlot Casino Erfahrungen okay nur Umsatz beim Bonus ist schon ordentlich. Ohne Bonus würde ich wieder einzahlen", "Erik"],
  ],
  haz: [
    ["endlich kein 5 sek ding", 5, "12/10/2026", "HAZ Casino ohne deutsche Lizenz läuft ohne diese 5 Sekunden Pause. Anmeldung ging fix und keine Probleme beim Spielen", "Tommy"],
    ["auszahlung kam sonntag", 4, "31/08/2026", "HAZ Casino Auszahlung in Krypto sogar am Sonntag bekommen. Support Antwort war bisschen knapp aber hat gereicht", "Mert"],
  ],
  luckyelf: [
    ["20 spins waren da", 5, "07/10/2026", "LuckyElf Casino Bonus ohne Einzahlung mit Code genutzt. 20 Spins kamen direkt hab daraus immerhin 18 Euro gemacht", "sina89"],
    ["auszahlung brauchte kyc", 4, "15/09/2026", "LuckyElf Casino Auszahlung ging erst nach Verifizierung. Danach 1 Tag bis Skrill also kann nicht meckern", "Patrick"],
    ["riesen bonus aber lang", 3, "02/07/2026", "LuckyElf Casino Erfahrungen: Auswahl gut und Seite schnell aber den großen Bonus umzusetzen dauert schon echt lang", "Uwe"],
  ],
  gioo: [
    ["login und spielen easy", 4, "04/10/2026", "Gioo Casino Login ging direkt ohne nervige Umwege. Hab paar NetEnt Slots gespielt und später 90 Euro ausgezahlt", "basti"],
  ],
  skycrown: [
    ["auszahlung am nächsten tag", 5, "21/10/2026", "SkyCrown Casino Auszahlung gestern Mittag beantragt heute früh auf Skrill. KYC hatte ich schon vorher gemacht", "Daniela"],
    ["gute mobile seite", 4, "30/09/2026", "SkyCrown Casino App brauchts eigentlich nicht die mobile Seite läuft schnell und merkt sich den Login", "Marco"],
    ["bonus hat gepasst", 4, "17/08/2026", "SkyCrown Casino Bonus aktiviert und Freispiele ohne Probleme bekommen. Bedingungen sind normal nix besonderes", "Nick"],
    ["support langsam abends", 3, "01/06/2026", "SkyCrown Casino Erfahrungen meist gut nur abends wartet man im Live Chat schon länger. Auszahlung kam aber an", "Heike"],
  ],
  scream: [
    ["war früher echt ok", 4, "12/03/2026", "Meine Scream Casino Erfahrungen waren damals gut vor allem die Live Games. Schade dass die Seite jetzt zu ist", "Frank"],
    ["auszahlung ging damals", 4, "08/01/2026", "Scream Casino Auszahlung hat bei mir früher 2 Tage gebraucht und kam immer an. Würde es sonst wieder nutzen", "Chris"],
  ],
};

const labels = {
  5: "Perfekt",
  4: "Sehr gut",
  3: "Durchschnitt",
  2: "Schlecht",
  1: "Furchtbar",
};

function stars(rating) {
  return Array.from({ length: 5 }, (_, index) =>
    `<span class="glsr-star glsr-star-${index < rating ? "full" : "empty"}" aria-hidden="true"></span>`
  ).join("");
}

function renderReview(slug, assignedPost, review, index) {
  const [title, rating, date, content, author] = review;
  return `<div class="glsr-review" data-type="local" data-source="oce-2026-batch" id="review-oce-${slug}-${index + 1}" data-assigned='{"assigned_posts":[${assignedPost}]}'>
    <div class="glsr-review-title"><h4 class="glsr-tag-value">${title}</h4></div>
    <div class="glsr-review-rating"><div class="glsr-star-rating glsr-stars" role="img" aria-label="Rated ${rating} out of 5 stars" data-rating="${rating}" data-reviews="0">${stars(rating)}</div></div> <div class="glsr-review-date"><span class="glsr-tag-value">${date}</span></div>
    <div class="glsr-review-content"><div class="glsr-tag-value" data-expanded="false"><p>${content}</p></div></div>
    <div class="glsr-review-author"><span class="glsr-tag-value">${author}</span></div>
</div>`;
}

function updateSummary(segment, ratings) {
  const count = ratings.length;
  const average = ratings.reduce((sum, rating) => sum + rating, 0) / count;
  const averageText = average.toFixed(1).replace(".", ",");
  const displayStars = Math.round(average);

  segment = segment.replace(
    /(<div class="glsr-summary-rating"><span class="glsr-tag-value">)[^<]+/,
    `$1${averageText}`
  );

  segment = segment.replace(
    /<div class="glsr-summary-stars"><div class="glsr-star-rating glsr-stars"[\s\S]*?<\/div><\/div>/,
    `<div class="glsr-summary-stars"><div class="glsr-star-rating glsr-stars" role="img" aria-label="Rated ${averageText} out of 5 stars based on ${count} ratings" data-rating="${averageText}" data-reviews="${count}">${stars(displayStars)}</div></div>`
  );

  segment = segment.replace(
    /(<div class="glsr-summary-text"><span class="glsr-tag-value">)[^<]+/,
    `$1${averageText} von 5 Sternen (basierend auf ${count} ${count === 1 ? "Bewertung" : "Bewertungen"})`
  );

  for (let rating = 1; rating <= 5; rating += 1) {
    const percentage = Math.round((ratings.filter((value) => value === rating).length / count) * 100);
    const pattern = new RegExp(
      `(<div class="glsr-bar" data-level=["']${rating}["']><span class="glsr-bar-label">${labels[rating]}</span><span class="glsr-bar-background"><span class="glsr-bar-background-percent" style="width:)[^%]+(%"></span></span><span class="glsr-bar-percent">)[^<]+`
    );
    segment = segment.replace(pattern, `$1${percentage}$2${percentage}%`);
  }

  return segment;
}

for (const [slug, newReviews] of Object.entries(reviewsByCasino)) {
  const filename = path.join(pagesRoot, slug, "_body.html");
  let html = fs.readFileSync(filename, "utf8");

  if (html.includes(`id="review-oce-${slug}-1"`)) {
    console.log(`${slug}: already updated`);
    continue;
  }

  const summaryStart = html.search(/<div class="glsr glsr-default"[^>]+data-shortcode=["']site_reviews_summary["']/);
  const formStart = html.search(/<div class="glsr glsr-default"[^>]+data-shortcode=["']site_reviews_form["']/);
  if (summaryStart < 0 || formStart < 0 || formStart <= summaryStart) {
    throw new Error(`${slug}: review summary or form not found`);
  }

  const summarySegment = html.slice(summaryStart, formStart);
  const assignedPostMatch = summarySegment.match(/data-assigned_posts=["'](\d+)["']/);
  if (!assignedPostMatch) {
    throw new Error(`${slug}: assigned post ID not found`);
  }
  const assignedPost = assignedPostMatch[1];

  const reviewsStart = html.search(/<div class="glsr glsr-default"[^>]+data-shortcode=["']site_reviews["']/);
  if (reviewsStart < 0) {
    throw new Error(`${slug}: reviews list not found`);
  }
  const nextHeading = html.indexOf("<h2", reviewsStart);
  const reviewsEnd = nextHeading >= 0 ? nextHeading : html.length;
  const reviewsSegment = html.slice(reviewsStart, reviewsEnd);
  const existingRatings = [...reviewsSegment.matchAll(/<div class="glsr-review"[\s\S]*?data-rating=["']([1-5])(?:,0)?["']/g)]
    .map((match) => Number(match[1]));
  const allRatings = [...existingRatings, ...newReviews.map((review) => review[1])];

  const updatedSummary = updateSummary(summarySegment, allRatings);
  html = html.slice(0, summaryStart) + updatedSummary + html.slice(formStart);

  const updatedReviewsStart = html.search(/<div class="glsr glsr-default"[^>]+data-shortcode=["']site_reviews["']/);
  const listStart = html.indexOf('<div class="glsr-reviews">', updatedReviewsStart);
  if (listStart < 0) {
    throw new Error(`${slug}: reviews container not found`);
  }
  const insertionPoint = listStart + '<div class="glsr-reviews">'.length;
  const cards = newReviews.map((review, index) => renderReview(slug, assignedPost, review, index)).join("\n");

  html = html.slice(0, insertionPoint)
    + `\n${cards}\n`
    + html.slice(insertionPoint).replace(/^\s*<p class="glsr-no-margins">Es gibt noch keine Kundenbewertungen\.<\/p>/, "");

  fs.writeFileSync(filename, html, "utf8");
  console.log(`${slug}: added ${newReviews.length} reviews`);
}
