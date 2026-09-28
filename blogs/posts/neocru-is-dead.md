# NeoCru is dead. Here's what it was.

**April 2026**

---

I built NeoCru in 2025 because recruitment felt broken from where I was standing.

Companies drowning in CVs they didn't have time to read. Good candidates rejected not because they weren't right but because nobody got to them in time. Recruiters spending hours on screening that felt like it should take minutes.

So I built something to fix it.

## What it was

NeoCru was an AI-powered recruitment tool. Companies posted a job, candidates applied, and NeoCru automatically evaluated every application against the actual requirements. It read both the CV and written answers, then generated a ranked shortlist with plain language explanations for every match, partial match, and gap.

No black box. No unexplained scores. Just: here's why this person fits, and here's why this one doesn't.

![NeoCru dashboard showing applicant evaluations for an AI Engineer role](neocru-dashboard.png)

It worked. I used it in a real hiring process at Allianz and it held up.

## How the evaluation worked

A company posts a job with actual requirements, not vibes. Candidates apply with a CV and written answers. The system evaluates every application against every requirement and produces a ranked shortlist where every rank comes with its reasoning: this requirement is met, this one partially, this one is missing.

The explanations were the real product decision. Recruiters don't trust a score of 82. They trust "four years of Python, no cloud experience, strong written motivation." An unexplained ranking gets second-guessed and re-screened by hand, which defeats the whole point. Explained rankings get acted on.

The AI did one more job on the other side of the table: generating proper job descriptions for companies that didn't have HR language in house. That was the niche, Dutch businesses running without a full HR setup. Too small for an applicant tracking system, too busy to screen properly.

## How it was built

Solo, but like a production system, because it was one.

Flask and PostgreSQL in the back, JavaScript dashboards in the front with role-based access for recruiters, OpenAI for the evaluation and the job-description generation. Everything ran on GCP: containerized Cloud Run services, Cloud Build for CI/CD, applicant CVs in Cloud Storage, structured logging throughout. The same deploy discipline I'd expect at work, applied to my own product.

That discipline was not overkill for a beta. It meant I could ship changes without fear, debug real user issues from logs instead of guesses, and hand a working product to strangers without babysitting it.

## Why I'm shutting it down

The product was real. The problem was real. But I'm a one person operation and the go-to-market for B2B SaaS is a different beast entirely. Getting companies to change their hiring process requires sales cycles, trust building, and time I don't have right now.

So I shut it down, and I shut it down properly. The decision came in December 2025. Users were notified, applicant data was removed, and the company was deregistered at the KVK. No zombie landing page, no dormant BV quietly accruing obligations. If you build things, kill them cleanly too; a half-dead product costs attention forever.

## What I learned

### The product is rarely the bottleneck

NeoCru worked. It survived a real hiring process. What it needed wasn't more features, it was sales cycles, trust building, and repeated conversations with companies about changing how they hire. That's a full-time job. I already had one. For solo B2B, distribution is the product, and I priced that at roughly zero when I started.

### Production discipline outlives the product

The company is gone; the patterns aren't. The Cloud Run and CI/CD setup, the structured logging, the habit of building so strangers can use it unattended, all of that moved straight into my later projects and my day job. Building it "properly" was the part of NeoCru that never died.

### Explanations are the AI feature

The model ranking candidates was table stakes. The model explaining each ranking in plain language was what made people trust it enough to use it. That lesson generalizes: for any AI system whose output a human must act on, the explanation is not documentation, it is the product.

### Shutting down is a skill

Deciding in December, notifying users, deleting data, and deregistering at the KVK took discipline that building never asks of you. I'd rather have one clean ending than three half-alive products. It also means the next idea starts with a clear desk.

If you used NeoCru during the beta, thank you. You helped me build something real.
