"""GitHub profile analyzer for extracting skills."""
import logging
import httpx
from collections import Counter

logger = logging.getLogger(__name__)

# Language to skill mapping
LANGUAGE_SKILLS = {
    "Python": ["Python", "Django", "FastAPI", "Flask"],
    "JavaScript": ["JavaScript", "Node.js", "React", "Vue.js"],
    "TypeScript": ["TypeScript", "Node.js", "React", "Angular"],
    "Java": ["Java", "Spring", "Maven"],
    "Kotlin": ["Kotlin", "Android"],
    "Go": ["Go", "Golang"],
    "Rust": ["Rust"],
    "C++": ["C++", "STL"],
    "C#": ["C#", ".NET", "ASP.NET"],
    "Ruby": ["Ruby", "Ruby on Rails"],
    "PHP": ["PHP", "Laravel"],
    "Swift": ["Swift", "iOS"],
    "Scala": ["Scala"],
    "Shell": ["Bash", "Shell scripting", "Linux"],
    "Dockerfile": ["Docker", "Containerization"],
    "HCL": ["Terraform", "Infrastructure as Code"],
    "YAML": ["CI/CD", "DevOps"],
}

# File patterns to detect technologies
TECH_PATTERNS = {
    "package.json": ["Node.js", "npm"],
    "requirements.txt": ["Python", "pip"],
    "Pipfile": ["Python", "Pipenv"],
    "pyproject.toml": ["Python", "Poetry"],
    "Cargo.toml": ["Rust", "Cargo"],
    "go.mod": ["Go", "Go Modules"],
    "pom.xml": ["Java", "Maven"],
    "build.gradle": ["Java", "Gradle"],
    "Gemfile": ["Ruby", "Bundler"],
    "composer.json": ["PHP", "Composer"],
    "docker-compose.yml": ["Docker", "Docker Compose"],
    "Dockerfile": ["Docker"],
    ".github/workflows": ["GitHub Actions", "CI/CD"],
    "Jenkinsfile": ["Jenkins", "CI/CD"],
    ".gitlab-ci.yml": ["GitLab CI", "CI/CD"],
    "terraform": ["Terraform", "IaC"],
    "kubernetes": ["Kubernetes", "K8s"],
    "k8s": ["Kubernetes", "K8s"],
    "ansible": ["Ansible"],
    "webpack.config": ["Webpack"],
    "vite.config": ["Vite"],
    "next.config": ["Next.js", "React"],
    "nuxt.config": ["Nuxt.js", "Vue.js"],
    "tsconfig.json": ["TypeScript"],
    ".eslintrc": ["ESLint"],
    "jest.config": ["Jest", "Testing"],
    "pytest.ini": ["pytest", "Testing"],
}


class GitHubAnalyzer:
    """Analyzes GitHub profile to extract skills and technologies."""

    def __init__(self, token: str | None = None):
        self.base_url = "https://api.github.com"
        self.token = token

    def _headers(self) -> dict:
        """Get headers for API requests."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def analyze(self, username: str) -> dict:
        """Analyze a GitHub profile."""
        async with httpx.AsyncClient() as client:
            # Get user info (for authenticated user, use /user endpoint)
            if self.token:
                # With token we can get the authenticated user's private info
                user_response = await client.get(
                    f"{self.base_url}/user",
                    headers=self._headers(),
                )
            else:
                user_response = await client.get(
                    f"{self.base_url}/users/{username}",
                    headers=self._headers(),
                )

            if user_response.status_code == 404:
                raise ValueError(f"GitHub user '{username}' not found")

            if user_response.status_code != 200:
                raise ValueError(f"GitHub API error: {user_response.status_code}")

            user_data = user_response.json()

            # Get repositories (with token - includes private repos)
            if self.token:
                repos_response = await client.get(
                    f"{self.base_url}/user/repos",
                    params={"per_page": 100, "sort": "updated", "affiliation": "owner"},
                    headers=self._headers(),
                )
            else:
                repos_response = await client.get(
                    f"{self.base_url}/users/{username}/repos",
                    params={"per_page": 100, "sort": "updated"},
                    headers=self._headers(),
                )

            repos = repos_response.json() if repos_response.status_code == 200 else []

            # Count private repos if using token
            private_repos_count = sum(1 for r in repos if r.get("private", False))

            # Analyze languages
            languages = Counter()
            for repo in repos:
                if repo.get("fork"):
                    continue  # Skip forks
                lang = repo.get("language")
                if lang:
                    languages[lang] += 1

            # Extract skills from languages
            skills = set()
            for lang, count in languages.most_common(10):
                if lang in LANGUAGE_SKILLS:
                    skills.update(LANGUAGE_SKILLS[lang])

            # Analyze repo names and descriptions for technologies
            for repo in repos[:20]:  # Top 20 repos
                name = repo.get("name", "").lower()
                desc = (repo.get("description") or "").lower()
                topics = repo.get("topics", [])

                # Check topics
                for topic in topics:
                    topic_lower = topic.lower()
                    if "react" in topic_lower:
                        skills.add("React")
                    elif "vue" in topic_lower:
                        skills.add("Vue.js")
                    elif "angular" in topic_lower:
                        skills.add("Angular")
                    elif "docker" in topic_lower:
                        skills.add("Docker")
                    elif "kubernetes" in topic_lower or "k8s" in topic_lower:
                        skills.add("Kubernetes")
                    elif "machine-learning" in topic_lower or "ml" in topic_lower:
                        skills.add("Machine Learning")
                    elif "deep-learning" in topic_lower:
                        skills.add("Deep Learning")
                    elif "tensorflow" in topic_lower:
                        skills.add("TensorFlow")
                    elif "pytorch" in topic_lower:
                        skills.add("PyTorch")
                    elif "fastapi" in topic_lower:
                        skills.add("FastAPI")
                    elif "django" in topic_lower:
                        skills.add("Django")
                    elif "flask" in topic_lower:
                        skills.add("Flask")
                    elif "postgres" in topic_lower:
                        skills.add("PostgreSQL")
                    elif "mongodb" in topic_lower:
                        skills.add("MongoDB")
                    elif "redis" in topic_lower:
                        skills.add("Redis")
                    elif "graphql" in topic_lower:
                        skills.add("GraphQL")
                    elif "rest" in topic_lower or "api" in topic_lower:
                        skills.add("REST API")

                # Check description keywords
                tech_keywords = {
                    "machine learning": "Machine Learning",
                    "deep learning": "Deep Learning",
                    "neural network": "Neural Networks",
                    "nlp": "NLP",
                    "computer vision": "Computer Vision",
                    "data science": "Data Science",
                    "data analysis": "Data Analysis",
                    "api": "REST API",
                    "microservice": "Microservices",
                    "serverless": "Serverless",
                    "aws": "AWS",
                    "gcp": "Google Cloud",
                    "azure": "Azure",
                    "ci/cd": "CI/CD",
                    "devops": "DevOps",
                }

                for keyword, skill in tech_keywords.items():
                    if keyword in desc:
                        skills.add(skill)

            # Add general skills
            if len(repos) > 0:
                skills.add("Git")
                skills.add("GitHub")

            if len(repos) > 10:
                skills.add("Version Control")

            return {
                "username": user_data.get("login", username),
                "name": user_data.get("name") or username,
                "bio": user_data.get("bio"),
                "public_repos": user_data.get("public_repos", 0),
                "private_repos_analyzed": private_repos_count,
                "followers": user_data.get("followers", 0),
                "languages": [lang for lang, _ in languages.most_common(10)],
                "skills": sorted(list(skills)),
                "repos_analyzed": len(repos),
                "has_token": bool(self.token),
            }
