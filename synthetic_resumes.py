from __future__ import annotations

from io import BytesIO
import random
import re
import zipfile

import pymupdf as fitz


FIRST_NAMES = (
    "Avery", "Jordan", "Morgan", "Riley", "Casey", "Taylor", "Quinn", "Cameron",
    "Jamie", "Parker", "Reese", "Rowan", "Skyler", "Drew", "Emerson", "Finley",
    "Hayden", "Kendall", "Logan", "Sage",
)
LAST_NAMES = (
    "Bennett", "Carter", "Dawson", "Ellis", "Foster", "Grayson", "Hayes", "Irwin",
    "Jordan", "Kim", "Lane", "Morris", "Nolan", "Owens", "Patel", "Quincy",
    "Reed", "Sawyer", "Turner", "Wells",
)
CITIES = (
    "Portland, Oregon", "Madison, Wisconsin", "Raleigh, North Carolina",
    "Denver, Colorado", "Pittsburgh, Pennsylvania", "Austin, Texas",
    "Minneapolis, Minnesota", "Providence, Rhode Island", "Boise, Idaho",
    "Richmond, Virginia",
)
COMPANIES = (
    "Cedar Ridge Solutions", "Blue Harbor Works", "Juniper Field Group",
    "Clearwater Systems", "Summit Grove Partners", "Brightpath Cooperative",
    "Copperline Services", "Evergreen Bridge Labs", "Westlake Innovation",
    "Maple Street Ventures",
)
DEGREES = (
    "Bachelor of Science", "Bachelor of Arts", "Master of Science",
    "Bachelor of Engineering", "Master of Business Administration",
)
SCHOOLS = (
    "Lakeview State University", "North Valley Institute", "Pinecrest College",
    "Western Lakes University", "Redwood Technical University",
)

ROLES = (
    {
        "title": "Data Scientist",
        "skills": ("Python", "SQL", "statistical modeling", "feature engineering", "scikit-learn",
                   "data visualization", "experiment design", "forecasting", "data quality",
                   "pandas", "model evaluation", "stakeholder communication"),
        "domains": ("retail planning", "customer operations", "public services", "supply chain"),
        "work": ("built a forecasting workflow", "evaluated classification approaches",
                 "organized event-level datasets", "reviewed model drift and data quality"),
        "outcomes": ("more reliable demand estimates", "faster case prioritization",
                     "clearer operational reporting", "better visibility into service trends"),
        "tools": ("Python and SQL", "pandas and scikit-learn", "notebooks and visualization tools",
                  "versioned data pipelines"),
        "project": "Service Demand Forecast",
    },
    {
        "title": "Accountant",
        "skills": ("general ledger", "account reconciliations", "month-end close", "Excel",
                   "variance analysis", "accounts payable", "accounts receivable", "audit support",
                   "financial reporting", "internal controls", "budget tracking", "documentation"),
        "domains": ("professional services", "community programs", "regional distribution",
                    "subscription operations"),
        "work": ("standardized the month-end close checklist", "reconciled high-volume accounts",
                 "reviewed supporting schedules", "improved the invoice review process"),
        "outcomes": ("more timely financial statements", "fewer unresolved reconciling items",
                     "clearer budget ownership", "stronger audit traceability"),
        "tools": ("Excel and general-ledger systems", "reconciliation workbooks",
                  "documented close controls", "reporting and billing platforms"),
        "project": "Close Process Improvement",
    },
    {
        "title": "Python Developer",
        "skills": ("Python", "REST APIs", "pytest", "FastAPI", "Django", "SQL", "Git",
                   "code review", "data modeling", "Linux", "CI pipelines", "technical writing"),
        "domains": ("workflow automation", "internal operations", "customer platforms",
                    "data integration"),
        "work": ("delivered a maintainable service", "automated a recurring workflow",
                 "refactored a high-change module", "improved API observability"),
        "outcomes": ("more predictable releases", "fewer manual processing steps",
                     "clearer service behavior", "simpler support handoffs"),
        "tools": ("Python and FastAPI", "Django and PostgreSQL", "pytest and CI pipelines",
                  "Git and container-based development"),
        "project": "Workflow Automation Service",
    },
    {
        "title": "Civil Engineer",
        "skills": ("site design", "AutoCAD", "grading plans", "drainage analysis", "survey review",
                   "quantity estimates", "construction documents", "permit coordination",
                   "quality assurance", "field inspections", "technical reports", "safety planning"),
        "domains": ("municipal infrastructure", "site development", "transportation access",
                    "stormwater planning"),
        "work": ("coordinated a site-design package", "reviewed field conditions",
                 "updated construction documentation", "supported permit submissions"),
        "outcomes": ("fewer design coordination gaps", "clearer contractor instructions",
                     "more dependable review cycles", "better documented field decisions"),
        "tools": ("AutoCAD and GIS", "design standards and calculation sheets",
                  "survey data and field notes", "project schedules and review logs"),
        "project": "Neighborhood Access Upgrade",
    },
    {
        "title": "HR Specialist",
        "skills": ("recruiting coordination", "onboarding", "HRIS", "employee relations",
                   "benefits administration", "policy documentation", "interview scheduling",
                   "training logistics", "confidential records", "workforce reporting",
                   "process improvement", "manager support"),
        "domains": ("health services", "distributed teams", "education programs",
                    "professional organizations"),
        "work": ("simplified a candidate coordination process", "updated onboarding materials",
                 "organized employee-service requests", "improved recurring workforce reports"),
        "outcomes": ("more consistent new-hire experiences", "faster request routing",
                     "clearer policy guidance", "better hiring-team coordination"),
        "tools": ("HRIS and applicant tracking systems", "secure case-management tools",
                  "spreadsheet reporting", "documented process checklists"),
        "project": "New-Hire Experience Refresh",
    },
    {
        "title": "Java Developer",
        "skills": ("Java", "Spring Boot", "REST APIs", "JUnit", "SQL", "microservices",
                   "message queues", "Git", "CI/CD", "application monitoring", "code review",
                   "system design"),
        "domains": ("account servicing", "order management", "business integration",
                    "customer support systems"),
        "work": ("implemented a resilient service endpoint", "reduced coupling between modules",
                 "strengthened integration tests", "improved production diagnostics"),
        "outcomes": ("more stable service releases", "clearer failure handling",
                     "faster incident investigation", "simpler integration maintenance"),
        "tools": ("Java and Spring Boot", "JUnit and test containers",
                  "SQL and message queues", "CI pipelines and monitoring dashboards"),
        "project": "Account Service Modernization",
    },
    {
        "title": "React Developer",
        "skills": ("React", "TypeScript", "JavaScript", "HTML", "CSS", "accessibility",
                   "component design", "API integration", "Jest", "responsive layouts",
                   "design systems", "browser testing"),
        "domains": ("customer self-service", "internal dashboards", "online education",
                    "service management"),
        "work": ("created a reusable interface pattern", "improved client-side form feedback",
                 "connected a dashboard to service APIs", "addressed accessibility findings"),
        "outcomes": ("more consistent user interactions", "fewer avoidable input errors",
                     "clearer status visibility", "better keyboard navigation"),
        "tools": ("React and TypeScript", "browser developer tools",
                  "Jest and component testing", "design-system documentation"),
        "project": "Accessible Service Dashboard",
    },
    {
        "title": "Banking Analyst",
        "skills": ("financial analysis", "credit review", "portfolio monitoring", "Excel",
                   "risk documentation", "customer due diligence", "policy interpretation",
                   "reconciliation", "data validation", "report writing", "process controls",
                   "client communication"),
        "domains": ("small-business banking", "consumer lending", "regional portfolios",
                    "branch operations"),
        "work": ("prepared consistent portfolio reviews", "validated source documentation",
                 "organized exception follow-up", "improved recurring risk summaries"),
        "outcomes": ("clearer review decisions", "more complete case records",
                     "faster exception resolution", "better portfolio visibility"),
        "tools": ("Excel and reporting systems", "documented review checklists",
                  "secure case-management systems", "policy and procedure libraries"),
        "project": "Portfolio Review Standardization",
    },
    {
        "title": "DevOps Engineer",
        "skills": ("Linux", "Docker", "Kubernetes", "CI/CD", "cloud infrastructure",
                   "infrastructure as code", "monitoring", "incident response", "Python",
                   "secrets management", "release automation", "runbook writing"),
        "domains": ("application platforms", "data services", "multi-team delivery",
                    "internal developer tooling"),
        "work": ("standardized a deployment workflow", "improved service health dashboards",
                 "automated environment provisioning", "strengthened incident handoffs"),
        "outcomes": ("more repeatable deployments", "faster recovery coordination",
                     "less configuration drift", "clearer service ownership"),
        "tools": ("Linux and container tooling", "CI/CD and infrastructure-as-code tools",
                  "metrics and log dashboards", "version-controlled runbooks"),
        "project": "Reliable Release Pipeline",
    },
    {
        "title": "Product Manager",
        "skills": ("product discovery", "roadmap planning", "user research", "prioritization",
                   "requirements writing", "analytics", "stakeholder alignment", "experimentation",
                   "backlog management", "release planning", "customer interviews", "documentation"),
        "domains": ("workflow products", "customer support tools", "business software",
                    "self-service experiences"),
        "work": ("translated user feedback into a roadmap", "clarified an ambiguous product workflow",
                 "aligned partners on release scope", "introduced outcome-focused review"),
        "outcomes": ("more focused delivery plans", "clearer customer journeys",
                     "better cross-team decisions", "more measurable product outcomes"),
        "tools": ("product analytics and research notes", "roadmap and backlog tools",
                  "workflow diagrams and prototypes", "release dashboards and documentation"),
        "project": "Customer Workflow Simplification",
    },
)


def _bullet(rng: random.Random, role: dict[str, object], index: int) -> str:
    work = rng.choice(role["work"])
    outcome = rng.choice(role["outcomes"])
    tools = rng.choice(role["tools"])
    domain = rng.choice(role["domains"])
    metric = rng.choice((12, 16, 19, 23, 27, 31, 35))
    audiences = ("team leads", "operations partners", "technical colleagues", "program owners")
    methods = (
        "documented assumptions and edge cases",
        "added review checkpoints and clear ownership",
        "paired with subject-matter experts before rollout",
        "tracked follow-up work through a shared action log",
    )
    return (
        f"{work.capitalize()} for {domain}, coordinating with {rng.choice(audiences)} to "
        f"confirm requirements and define practical acceptance criteria. Applied {tools} to "
        f"deliver {rng.choice(('a repeatable process', 'a measured improvement', 'a clearer workflow'))}; "
        f"{rng.choice(methods)}. The effort contributed to {outcome}, with a {metric}% "
        f"improvement in the selected team measure and documented follow-up for future reviews."
    )


def build_resume(index: int) -> tuple[str, str, str]:
    rng = random.Random(20261119 + index)
    role = ROLES[index % len(ROLES)]
    first = FIRST_NAMES[index // len(LAST_NAMES)]
    last = LAST_NAMES[index % len(LAST_NAMES)]
    name = f"{first} {last}"
    email_name = f"{first.lower()}.{last.lower()}.{index + 1:03d}"
    years = 5 + (index % 10)
    skill_a, skill_b, skill_c = rng.sample(role["skills"], 3)
    domain = rng.choice(role["domains"])

    summary = (
        f"Fictional {role['title']} with {years} years of experience supporting {domain} "
        f"and cross-functional delivery. Brings practical strength in {skill_a}, {skill_b}, "
        f"and {skill_c}, with a steady focus on understandable decisions and dependable "
        f"follow-through. Comfortable turning broad requests into scoped work, checking "
        f"assumptions with the people closest to a process, and sharing progress in plain "
        f"language. Known in these sample materials for thoughtful documentation, constructive "
        f"collaboration, and a habit of measuring whether a change improved day-to-day work. "
        f"Interested in roles where careful analysis and reliable execution support meaningful "
        f"service outcomes."
    )

    role_sections = []
    for experience_index in range(3):
        company = COMPANIES[(index + experience_index * 3) % len(COMPANIES)]
        years_ago = (experience_index + 1) * 2
        job_title = role["title"] if experience_index == 0 else (
            f"Associate {role['title']}" if experience_index == 1 else f"Junior {role['title']}"
        )
        bullets = [_bullet(rng, role, experience_index * 3 + n) for n in range(3)]
        role_sections.append(
            f"{job_title} | {company} | {CITIES[(index + experience_index) % len(CITIES)]} "
            f"| {years_ago} years\n" + "\n".join(f"- {bullet}" for bullet in bullets)
        )

    projects = []
    for project_index in range(2):
        tools = rng.choice(role["tools"])
        outcome = rng.choice(role["outcomes"])
        projects.append(
            f"{role['project']} {project_index + 1}: Partnered with a small working group to "
            f"map the current process, identify its highest-friction handoffs, and agree on "
            f"a practical improvement plan. Used {tools} to build and review a modest "
            f"proof of concept, then gathered feedback from intended users before documenting "
            f"next steps. The work clarified ownership, surfaced operational risks early, and "
            f"created a reusable reference for similar efforts. The resulting approach supported "
            f"{outcome} without relying on unsupported claims or unverified production metrics."
        )

    skills_text = ", ".join(role["skills"])
    education = (
        f"{rng.choice(DEGREES)} in {rng.choice(('Information Systems', 'Business', 'Engineering', 'Statistics', 'Operations'))} "
        f"| {rng.choice(SCHOOLS)} | {2012 + index % 12}\n"
        f"Professional learning: {rng.choice(role['skills'])} practice, "
        f"{rng.choice(role['skills'])} workshops, and ongoing study of {domain}."
    )
    page_one = (
        f"{name.upper()}  |  {role['title']}\n"
        "SYNTHETIC SAMPLE — NOT A REAL PERSON\n"
        f"{CITIES[index % len(CITIES)]}  |  {email_name}@example.test  |  (555) 010-{index:04d}\n\n"
        f"PROFESSIONAL SUMMARY\n{summary}\n\n"
        f"CORE SKILLS\n{skills_text}\n\n"
        f"PROFESSIONAL EXPERIENCE\n{role_sections[0]}\n\n"
        f"{role_sections[1].splitlines()[0]}\n"
        + role_sections[1].splitlines()[1]
    )
    page_two = (
        f"{'\n'.join(role_sections[1].splitlines()[2:])}\n\n"
        f"{role_sections[2]}\n\n"
        f"SELECTED PROJECTS\n{projects[0]}\n\n{projects[1]}\n\n"
        f"EDUCATION AND CONTINUING LEARNING\n{education}\n\n"
        "WORKING APPROACH\n"
        f"Prioritizes clear handoffs, respectful collaboration, and appropriately scoped "
        f"solutions. Uses {skill_a} and {skill_b} as job-related tools, validates details "
        f"before sharing conclusions, and treats feedback as a way to improve the next "
        f"iteration. All names, histories, organizations, and contact details in this file "
        f"are fictional examples created for software testing."
    )
    full_text = f"{page_one}\n{page_two}"
    word_count = len(re.findall(r"\b[\w'-]+\b", full_text))
    if not 800 <= word_count <= 1200:
        raise ValueError(f"Generated resume {index + 1} has {word_count} words, outside target.")
    return name, page_one, page_two


def _add_page(document: fitz.Document, text: str, fontsize: float = 8.5) -> None:
    page = document.new_page(width=595, height=842)
    rect = fitz.Rect(42, 38, 553, 804)
    remaining_height = page.insert_textbox(
        rect,
        text,
        fontname="helv",
        fontsize=fontsize,
        lineheight=1.1,
        color=(0.12, 0.16, 0.2),
    )
    if remaining_height < 0:
        raise ValueError("Resume text does not fit on two pages at a readable font size.")


def create_resume_archive() -> bytes:
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(
            "README.txt",
            "100 fictional resumes for testing resume-search software.\n"
            "Every person, organization, work history, and contact detail is synthetic.\n"
            "Each PDF is two pages and approximately 800-1,200 words.\n",
        )
        for index in range(100):
            name, page_one, page_two = build_resume(index)
            document = fitz.open()
            _add_page(document, page_one)
            _add_page(document, page_two)
            pdf_bytes = document.tobytes()
            document.close()
            role_name = re.sub(r"[^a-z0-9]+", "_", ROLES[index % len(ROLES)]["title"].lower()).strip("_")
            pdf_path = f"resumes/{index + 1:03d}_{role_name}.pdf"
            zip_file.writestr(pdf_path, pdf_bytes)
    return archive.getvalue()
