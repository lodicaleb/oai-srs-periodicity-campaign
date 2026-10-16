# Create GitHub repository

This folder is already a valid collection of Git-ready source files. Create the **remote** repository privately first (suggested name `oai-srs-periodicity-campaign`), then upload all files (excluding ignored files).

### With Git CLI

```bash
# From the extracted root of this repository:
git init
git add .
git commit -m "Document OAI 5G NR SRS periodicity campaign"
git branch -M main
# Create an empty private repo in GitHub web, then:
git remote add origin https://github.com/YOUR_USERNAME/oai-srs-periodicity-campaign.git
git push -u origin main
```

### With GitHub CLI (optional)

```bash
# Requires GitHub CLI and interactive authentication:
gh auth login
gh repo create oai-srs-periodicity-campaign --private --source=. --remote=origin --push
```

Do not run `git init` again if the folder already includes `.git`. The remote URL is an example; substitute your actual GitHub username. The public-vs-private choice and the final license belong to the repository owner.
