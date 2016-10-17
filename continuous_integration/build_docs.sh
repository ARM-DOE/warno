#!/bin/bash
# Adapted from the ci/build_docs.sh file from the pyart project
# https://github.com/ARM-DOE/pyart

set -e

cd "$TRAVIS_BUILD_DIR"
source "$TRAVIS_BUILD_DIR"/utility_setup_scripts/set_vagrant_env.sh

echo "Building Docs"
conda install --yes sphinx numpydoc

mv "$TRAVIS_BUILD_DIR"/doc /tmp
cd /tmp/doc
# mv -f src/index.ci src/index.rst
make html

# upload to warno-docs-travis repo if this is not a pull request and
# secure token is available
if [ "$TRAVIS_PULL_REQUEST" == "false" ] && [ "$TRAVIS_BRANCH" == "ar104_autobuild_docs" ] && [ $TRAVIS_SECURE_ENV_VARS == 'true' ]; then
    cd /tmp/doc/build/html
    git config --global user.email "warno-docs-bot@example.com"
    git config --global user.name "warno-docs-bot"

    git init
    touch README
    git add README
    git commit -m "Initial commit" --allow-empty
    git branch gh-pages
    git checkout gh-pages
    touch .nojekyll
    git add --all .
    git commit -m "Version" --allow-empty
    git remote add origin https://$GH_TOKEN@overwatch.pnl.gov/hard505/warno-vagrant.git &> /dev/null
    git push origin gh-pages -fq &> /dev/null
fi

exit 0