const setText = (id, value) => {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value || "";
    }
};

const setLink = (id, href, fallbackText) => {
    const element = document.getElementById(id);
    if (!element) {
        return;
    }
    if (href) {
        element.setAttribute("href", href);
        element.removeAttribute("aria-disabled");
        element.textContent = fallbackText || element.textContent;
    } else {
        element.setAttribute("href", "#");
        element.setAttribute("aria-disabled", "true");
    }
};

const renderList = (items) => {
    const list = document.createElement("ul");
    items.forEach((item) => {
        const text = typeof item === "string" ? item : item?.text;
        if (!text) {
            return;
        }
        const li = document.createElement("li");
        li.textContent = text;
        list.appendChild(li);
    });
    return list;
};

const renderCards = (container, cards) => {
    container.innerHTML = "";
    cards.forEach((card) => {
        container.appendChild(card);
    });
};

const createSkillBubble = (skill, onClick) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "skill-chip";
    button.textContent = skill;
    button.addEventListener("click", () => onClick(skill, button));
    return button;
};

const createDomainCard = (domain, onSkillClick) => {
    const card = document.createElement("article");
    card.className = "domain-card";

    const h3 = document.createElement("h3");
    h3.textContent = domain.label;

    const p = document.createElement("p");
    p.textContent = domain.description;

    const skillList = document.createElement("div");
    skillList.className = "skill-chip-list";
    (domain.skills || []).forEach((skill) => {
        skillList.appendChild(createSkillBubble(skill, onSkillClick));
    });

    card.appendChild(h3);
    card.appendChild(p);
    card.appendChild(skillList);

    return card;
};

const createSkillsCard = (title, bullets) => {
    const card = document.createElement("div");
    card.className = "skills-card";

    const h3 = document.createElement("h3");
    h3.textContent = title;

    card.appendChild(h3);
    card.appendChild(renderList(bullets));

    return card;
};

const createExperienceItem = (experience) => {
    const item = document.createElement("div");
    item.className = "timeline-item";

    const header = document.createElement("div");
    header.className = "timeline-header";

    const company = document.createElement("h3");
    company.textContent = experience.company + (experience.location ? `, ${experience.location}` : "");

    const timeframe = document.createElement("span");
    timeframe.textContent = experience.timeframe;

    header.appendChild(company);
    header.appendChild(timeframe);

    item.appendChild(header);

    if (experience.notes) {
        const note = document.createElement("p");
        note.textContent = experience.notes;
        item.appendChild(note);
    }

    experience.roles.forEach((role) => {
        const roleTitle = document.createElement("h4");
        roleTitle.textContent = `${role.title} (${role.timeframe})`;
        item.appendChild(roleTitle);
        item.appendChild(renderList(role.bullets));
    });

    return item;
};

const createProjectCard = (project) => {
    const card = document.createElement("article");
    card.className = "project-card";

    const h3 = document.createElement("h3");
    h3.textContent = project.name;

    const timeframe = document.createElement("span");
    timeframe.className = "project-time";
    timeframe.textContent = project.timeframe;

    const bullets = renderList(project.bullets);

    card.appendChild(h3);
    card.appendChild(timeframe);
    card.appendChild(bullets);

    const projectLinks = {
        "Thesis - Predicting Perceptions of Dutch Company Names": "https://github.com/hiwafeizi/thesis",
        "Group Thesis - Multimodal Speech Recognition with AV-HuBERT": "https://github.com/hiwafeizi/research-workshop/tree/main",
        "Software Engineering Course - PetMatters": "https://github.com/hiwafeizi/SE4CSAI-Project",
        "C++ Course Project - Battle-C": "https://github.com/hiwafeizi/Battle-C",
        "AI for Nature and Environment Project": "https://github.com/hiwafeizi/AI4NE"
    };

    const link = projectLinks[project.name];
    if (link) {
        const anchor = document.createElement("a");
        anchor.className = "project-link";
        anchor.href = link;
        anchor.target = "_blank";
        anchor.rel = "noreferrer";
        anchor.textContent = "View Code";
        card.appendChild(anchor);
    }

    return card;
};

const createEducationCard = (education) => {
    const card = document.createElement("div");
    card.className = "education-card";

    const h3 = document.createElement("h3");
    h3.textContent = education.degree;

    const p = document.createElement("p");
    p.textContent = education.institution;

    const span = document.createElement("span");
    span.textContent = education.timeframe;

    card.appendChild(h3);
    card.appendChild(p);
    card.appendChild(span);

    return card;
};

const createEvidenceCard = (item) => {
    const card = document.createElement("div");
    card.className = "evidence-card";

    const meta = document.createElement("div");
    meta.className = "evidence-meta";
    meta.textContent = [item.project, item.company, item.role]
        .filter(Boolean)
        .join(" · ");

    const text = document.createElement("p");
    text.textContent = item.text;

    card.appendChild(meta);
    card.appendChild(text);

    if (item.timeframe) {
        const time = document.createElement("div");
        time.className = "evidence-time";
        time.textContent = item.timeframe;
        card.appendChild(time);
    }

    return card;
};

const buildSkillIndex = (data) => {
    const index = new Map();

    const addSkillItem = (skill, item) => {
        const key = (skill || "").trim();
        if (!key) {
            return;
        }
        if (!index.has(key)) {
            index.set(key, []);
        }
        index.get(key).push(item);
    };

    if (Array.isArray(data?.skillEvidence) && data.skillEvidence.length > 0) {
        data.skillEvidence.forEach((entry) => {
            if (!entry || !entry.skill) {
                return;
            }
            index.set(entry.skill, entry.items || []);
        });
        return index;
    }

    (data?.experience || []).forEach((entry) => {
        (entry.roles || []).forEach((role) => {
            (role.bullets || []).forEach((bullet) => {
                const detail = typeof bullet === "string" ? { text: bullet, skills: [] } : bullet;
                (detail.skills || []).forEach((skill) => {
                    addSkillItem(skill, {
                        text: detail.text,
                        project: detail.project,
                        company: entry.company,
                        role: role.title,
                        timeframe: role.timeframe
                    });
                });
            });
        });
    });

    (data?.projects || []).forEach((project) => {
        (project.bullets || []).forEach((bullet) => {
            const detail = typeof bullet === "string" ? { text: bullet, skills: [] } : bullet;
            (detail.skills || []).forEach((skill) => {
                addSkillItem(skill, {
                    text: detail.text,
                    project: project.name,
                    company: null,
                    role: "Project",
                    timeframe: project.timeframe
                });
            });
        });
    });

    return index;
};

const loadResume = async () => {
    const response = await fetch("resume.json");
    if (!response.ok) {
        return;
    }

    const data = await response.json();

    document.title = `${data.name} | ${data.title}`;
    setText("hero-name", data.name);
    setText("hero-subtitle", data.tagline || "Designing scalable data systems, full-stack products, and applied AI automation.");
    setText("hero-location", data.location);
    setText("hero-email", data.email);
    setText("summary-text", data.summary);
    const skillIndex = buildSkillIndex(data);
    const skillsContainer = document.getElementById("skills-container");
    const evidenceModal = document.getElementById("evidence-modal");
    const evidenceSkill = document.getElementById("evidence-skill");
    const evidenceList = document.getElementById("evidence-list");
    const evidenceEmpty = document.getElementById("evidence-empty");
    const evidenceClose = document.getElementById("evidence-close");
    const evidenceBackdrop = document.querySelector("[data-evidence-close]");

    const openEvidence = (skill) => {
        if (!evidenceModal || !evidenceSkill || !evidenceList || !evidenceEmpty) {
            return;
        }

        evidenceSkill.textContent = skill;
        evidenceList.innerHTML = "";

        const items = skillIndex.get(skill) || [];
        items.forEach((item) => {
            evidenceList.appendChild(createEvidenceCard(item));
        });

        evidenceEmpty.classList.toggle("visible", items.length === 0);
        evidenceModal.classList.add("active");
        evidenceModal.setAttribute("aria-hidden", "false");
        document.body.classList.add("no-scroll");
    };

    const closeEvidence = () => {
        if (!evidenceModal) {
            return;
        }
        evidenceModal.classList.remove("active");
        evidenceModal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("no-scroll");
    };

    if (evidenceClose) {
        evidenceClose.addEventListener("click", closeEvidence);
    }

    if (evidenceBackdrop) {
        evidenceBackdrop.addEventListener("click", closeEvidence);
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeEvidence();
        }
    });

    if (skillsContainer && Array.isArray(data.domains)) {
        const cards = data.domains.map((domain) => createDomainCard(domain, (skill) => {
            openEvidence(skill);
        }));
        renderCards(skillsContainer, cards);
    }

    const experienceContainer = document.getElementById("experience-container");
    if (experienceContainer && Array.isArray(data.experience)) {
        renderCards(
            experienceContainer,
            data.experience.map((entry) => createExperienceItem(entry))
        );
    }

    const projectsContainer = document.getElementById("projects-container");
    if (projectsContainer && Array.isArray(data.projects)) {
        renderCards(
            projectsContainer,
            data.projects.map((entry) => createProjectCard(entry))
        );
    }

    const educationContainer = document.getElementById("education-container");
    if (educationContainer && Array.isArray(data.education)) {
        renderCards(
            educationContainer,
            data.education.map((entry) => createEducationCard(entry))
        );
    }

    setLink("contact-email", data.email ? `mailto:${data.email}` : "", "Email");
    setLink("contact-linkedin", data.links?.linkedin, "LinkedIn");
    setLink("contact-github", data.links?.github, "GitHub");
    setText("contact-location", data.location);
};

loadResume();

const initRecommendationCarousel = () => {
    const track = document.getElementById("recommendation-track");
    const prevButton = document.getElementById("recommendation-prev");
    const nextButton = document.getElementById("recommendation-next");
    if (!track) {
        return;
    }

    const cards = Array.from(track.children);
    if (cards.length === 0) {
        return;
    }

    let index = 0;

    const scrollToIndex = (nextIndex) => {
        const clamped = (nextIndex + cards.length) % cards.length;
        index = clamped;
        const card = cards[index];
        track.scrollTo({
            left: card.offsetLeft,
            behavior: "smooth"
        });
    };

    if (prevButton) {
        prevButton.addEventListener("click", () => scrollToIndex(index - 1));
    }

    if (nextButton) {
        nextButton.addEventListener("click", () => scrollToIndex(index + 1));
    }
};

initRecommendationCarousel();
