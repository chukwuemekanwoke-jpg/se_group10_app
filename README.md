# Clone the repo (defaults to develop)
git clone https://github.com/chukwuemekanwoke-jpg/se_group10_app.git
cd se_group10_app

# Create a feature
git checkout -b feature/login-authentication
# ... make changes ...
git add .
git commit -m "feat: add login system"
git push -u origin feature/login-authentication

# Create Peer Review on GitHub → Get approved → Merge to develop

# Deploy to staging for testing
git checkout staging
git pull origin staging
git merge develop
git push origin staging

# After testing, release to production
git checkout main
git pull origin main
git merge staging
git tag v1.1
git push origin main --tags