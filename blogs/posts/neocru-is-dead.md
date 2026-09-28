# NeoCru is dead. Here's what it was.

**April 2026**

**TL;DR.** I built an AI recruitment tool that screened every application against the job's actual requirements and explained every ranking. It got zero users, so I closed the company properly, KVK deregistration included. The site is still up at [neocru.nl](https://neocru.nl/) if you want to see what it was.

---

I built NeoCru in 2025 because recruitment felt broken from where I was standing.

Companies drowning in CVs they didn't have time to read. Good candidates rejected not because they weren't right but because nobody got to them in time. Recruiters spending hours on screening that felt like it should take minutes.

So I built something to fix it.

## What it was

NeoCru was an AI-powered recruitment tool. Companies posted a job, candidates applied, and NeoCru automatically evaluated every application against the actual requirements. It read both the CV and written answers, then generated a ranked shortlist with plain language explanations for every match, partial match, and gap.

No black box. No unexplained scores. Just: here's why this person fits, and here's why this one doesn't.

![NeoCru dashboard showing applicant evaluations for an AI Engineer role](neocru-dashboard.png)

Its one real-world result was an intern hire at Allianz: I found the candidate through NeoCru and introduced them, and they got hired. Allianz itself never used the platform, for GDPR reasons. So even its one success happened around the product, not through it.

## How it worked

A company posts a job with requirements. Candidates apply with a CV and written answers. The system checks every application against every requirement and returns a ranked shortlist where each rank carries its reasoning: met, partially met, missing. It could also generate the job description itself, for companies without HR language in house. The target was Dutch businesses running without a full HR setup.

## How it was built

Flask and PostgreSQL in the back, JavaScript dashboards with role-based access in the front, OpenAI for the evaluation and the job-description generation. Deployed on GCP: containerized Cloud Run services, Cloud Build for CI/CD, CVs in Cloud Storage, structured logging.

## Why I shut it down

I never got a user. Not a churned user, not an unhappy user: zero users.

The product ran, but getting Dutch companies to change how they hire takes sales cycles, trust, and time, and I was doing this next to a full-time job. The building part I could do solo. The distribution part I couldn't, and without distribution nothing else matters.

I decided in December 2025 and closed the company properly, KVK deregistration included. The site itself is still up at [neocru.nl](https://neocru.nl/), so you can go see exactly what it was.

## What I learned

### Distribution was the whole game

I spent my time on the product because that was the part I knew how to do. B2B SaaS doesn't die from bad products, it dies from nobody hearing about them. If I do this again, selling starts before building finishes.

### The patterns outlived the product

The Cloud Run and CI/CD setup, the structured logging, the habit of building things that run unattended: all of it carried into my later projects and my day job. The company is gone; the engineering isn't.

### Explanation-first was the right call, and I never got to prove it

Ranking with reasoning instead of bare scores was the core design bet. I still think it's right. With zero users, it stays an opinion.

### Ending it cleanly was cheap

Deciding and deregistering at the KVK took an afternoon. The site can stay up as a portfolio piece; the company obligations could not.
