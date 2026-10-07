# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->
FitFindr takes a plain-language request like "vintage graphic tee under $30, size M" and finds a matching item among secondhand listings from Depop, thredUp, and Poshmark. It suggests one or two outfits that pair the item with clothes the user already owns, then writes a short first-person caption they could post about the find. When nothing in the listings matches, the agent stops before calling the model and tells the user which part of the request to loosen. When the user has no saved wardrobe, it gives general styling advice and doesn't claim they own anything.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the listings by price ceiling and size, then ranks what's left by how many of the user's keywords appear in each listing's title, description, and style tags. It does not call the model.
- **Inputs:** <!-- name and type each: `max_price` (float), not "a price" --> searching critia or filer keywords
- **Returns:** A list of listing dicts (each with id, title, description, category, style_tags, size, condition, price, colors, brand, platform), best match first, at most config.SEARCH_RESULT_LIMIT items. Every item has price <= max_price when a ceiling is given.
- **When it has nothing:** Returns [], an empty list, never None and never an exception. The planning loop branches on this.
s whose title names the thing searched for.

### `suggest_outfit`

- **What it does:** It search through the users wardrobe that suggests a good fit based on the item returned form search listing.
- **Inputs:** new_item (dict) a single listing dict, the item the user is considering; wardrobe (dict) with an items key holding a list of wardrobe item dicts.
- **Returns:** A non-empty string with up to two outfits in no more than 100 words. Each outfit includes the new item, uses only pieces from the wardrobe, refers to them by their exact names, and gives one sentence on why it works. Wardrobe fields that are None (often notes) are left out of the prompt.
- **When it has nothing:** If wardrobe["items"] is empty, it returns general styling advice of 70 words or fewer, covering what to pair the item with, when to wear it, and why it works. Its instructions forbid claiming the user owns anything. The check is if not wardrobe["items"] and not if not wardrobe, because the empty wardrobe {"items": []} is itself truthy.

### `create_fit_card`

- **What it does:** Asks the model to write a short caption about the item and outfit, the way someone would post about a thrift find.
- **Inputs:** outfit (str) the text returned by suggest_outfit; new_item (dict) the listing dict for the item.
- **Returns:** returns an array of dictonary of [name, size, price and website]
- **When it has nothing:** A first-person caption of 2 to 4 sentences and no more than 80 words. It mentions the item once (in a shortened, natural form of the title), the platform once, and the exact price (formatted like $38.00) once, in the first or second sentence. It uses at least one of the item's style tags and one specific pairing from the outfit, doesn't address the reader or encourage buying, and uses only details from the prompt.provided, so no fit card could be made." without calling the model.

### `Search rules and limitations` 

- **Size rule:** The requested size and each listing size are lowercased, cut at (so XL (oversized) becomes xl), and stripped of spaces. A listing matches if the requested size equals its full size label or one of its /-separated parts. M matches M, S/M, and M/L. S does not match XS, XL (oversized), or US 9, which a plain substring check would accept. Numeric shoe sizes match only with the US prefix, and waist sizes like W30 L30 match only an exact request.

- **Keyword rule:** Query words are lowercased, stripped of punctuation, and filtered against a list of filler words (a, the, for, under, looking, and others) before scoring. Before this filter existed, "a sequin ballgown for prom" matched 10 unrelated listings through "a" and "for", so the empty-search branch could never fire. Listing words get the same punctuation stripping, which lets zip match "Full zip.".

- **limitation:** Scoring checks whether each keyword appears anywhere in the title, description, or tags. It ignores where the keyword appears, so items with the same tags tie and come back in file order. For "vintage graphic tee", the Y2K Baby Tee, the 2003 Tour Graphic Tee, and the Vintage Band Tee all score 3, and the Y2K tee ranks first only because it comes first in the file. Giving title matches extra weight would break these ties in favor of items whose title names the thing searched for.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If search_listings returns an empty list, the agent writes a message to session["error"] naming what the user searched for and one constraint to loosen: raise the price ceiling, drop the size, or try other keywords. It then returns the session without calling suggest_outfit or create_fit_card, so fit_card stays None. Otherwise it stores the first result in session["selected_item"] and continues to suggest_outfit, then create_fit_card.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** <!-- regex, string splitting, or asking the model — say which -->
With regex, in agent.py::parse_query. A dollar amount ($30, $12.50) becomes max_price, and the word "size" followed by a letter size (size m, size xxs) becomes size. The parser then removes those matched phrases, and the remaining text becomes the description. Finding and removing use the same pattern variables, so they always agree. Removing the whole matched phrase leaves letters inside other words alone: the "m" in "medium" or "denim" stays. A missing price or size is None, and its filter is skipped.

**What moves through the session:** <!-- which fields, in what order -->query → parsed (description, size, max_price) → search_results → branch → selected_item → outfit_suggestion → fit_card. Each tool reads its inputs from the session and writes its result back. suggest_outfit gets session["selected_item"] and session["wardrobe"], and create_fit_card gets session["outfit_suggestion"] and session["selected_item"]. The loop uses only the keys defined in new_session().

**Stop Condition:** A counter increases once per step, and trace.check_iterations(count) runs before each step, so the run stops with an error if the count ever passes config.MAX_ITERATIONS. The loop currently runs straight through and stays well under that limit. The guard covers retry logic added later.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->



**One full query**

```
$ python app.py ask 'vintage graphic tee under $30, size M'

```

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   ### Outfit 1
* **Top:** Y2K Baby Tee — Butterfly Print
* **Bottoms:** Baggy straight-leg jeans, dark wash
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

This balances the fitted Y2K tee with baggy denim and chunky sneakers.

### Outfit 2
* **Top:** Y2K Baby Tee — Butterfly Print
* **Outerwear:** Vintage black denim jacket
* **Bottoms:** Wide-leg khaki trousers
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

Layering the vintage denim jacket adds classic texture to the butterfly graphic.

  Fit card: I just found this cute butterfly baby tee on depop for $18.00. It fits right into my y2k wardrobe when I wear it with baggy straight-leg jeans in a dark wash and chunky white sneakers.



**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]

```
$ python -c "from tools import suggest_outfit; ..."

```
### Casual Streetwear
- Vintage Levi's 501 Jeans — Medium Wash
- White ribbed tank top
- Oversized grey crewneck sweatshirt
- Chunky white sneakers
- Black crossbody bag

This balances a fitted basic with a cozy oversized layer for an effortless streetwear look.

### Classic Denim
- Vintage Levi's 501 Jeans — Medium Wash
- White ribbed tank top
- Vintage black denim jacket
- Brown leather belt
- Black combat boots

```
$ python -c "from tools import create_fit_card; ..."

```
I just found these medium wash vintage Levi's 501 jeans on depop for $38.00. I love the denim look and how well they fit into my streetwear rotation. For an easy everyday outfit, I would style them with crisp white sneakers.

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->
I used Claude as a tutor throughout this unit. It reviewed my code, predicted what my tests would show, and explained Python and regex syntax I hadn't used before. For a few pieces it gave me working code after I'd been stuck on them: the stop word filter, and a simpler regex parser. Most of my learning came from running tests it suggested and getting results I didn't expect.

**Moment 1**

- *What I asked for:*A review of my search_listings, after a rewrite where the price filter, size matching, and scoring all looked right to me.
- *What came back:*Claude said there was still a bug, and had me predict and then run search_listings('a sequin ballgown for prom'). There's no ballgown in the data, but it returned 10 results. Every listing scored at least 1 because filler words like "a" and "for" appear in almost every description. That meant my empty-search branch could never fire, and criterion 2 would fail every time. Claude suggested a stop-word set and gave me the two lines that filter it out of the keywords.
- *What I changed:*I added the stop-word filter, but the result was still 10. Running grep on tools.py showed my old line keywords = set(description.lower().split()) was still underneath the new one and overwriting it. I deleted that line, then applied the same punctuation stripping to the listing words. Without it, a search for "zip" missed a jacket whose description says "Full zip.". After both changes, the ballgown query returned 0, 'for the' returned [], and 'zip' found both jackets.

**Moment 2**

- *What I asked for:*A check of suggest_outfit output against my own system-prompt rules, instead of just reading it and deciding it looked good.
- *What came back:*Every concrete rule was followed: two outfits, the new item in each, and wardrobe pieces named exactly as written. The one rule the model ignored was "brief", in both the full and empty wardrobe branches, where it wrote about 200 words with headers. Claude pointed out that "brief" was my only vague rule and the only one ignored. It's the same problem as a vague acceptance criterion: if I can't measure it, the model doesn't reliably follow it.
- *What I changed:*I replaced "brief" with word limits, at most 100 words for outfits and 70 for general advice, and specified that the limit includes headings and item names. I measured the results with wc -w instead of eyeballing them: 86 and 64 words. I used the same approach for create_fit_card, turning "sounds natural" into specific rules (first person, 2 to 4 sentences, price once in sentence one or two, don't address the reader), and checked them with grep.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
