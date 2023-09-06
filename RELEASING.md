# How to Release the SDK

1. Merge all the changes that need to go into the release to the master branch.
2. Open the `setup.py` file from the top level directory of the project.
3. Search for `version=` in the file to find the version number, for example `1.8.15`.
4. Create a pull request, get it reviewed and approved, and merge it after approval.
5. Check [test.pypi.org](https://test.pypi.org/project/wavefront-sdk-python) for a published package, make sure it's production ready.
6. From the root directory of the project in the master branch, run the following commands:
    1. `python -m venv venv`
    2. `source venv/bin/activate`
    3. `pip install -i https://test.pypi.org/simple/ wavefront-sdk-python`
7. Log in to GitHub, click **Releases** on the right, and click **Draft a new release**.
8. For **Choose a tag**, choose the version you found in step 3, and prefix it with `v` for example `v1.8.15`.  
   You need to enter the version where it says **Find or create new tag**.  
   ![A diagram that shows how to choose version](images/choose-version.png)
9. Provide a short but descriptive title for the release.
10. Fill in the details of the release. Please copy the markdown from the previous release and follow the same format.
11. Click **Publish release.** to start publishing the release to [pypi.org](https://pypi.org/).
12. From the GitHub top navigation bar of this project, click the **Actions** tab. On the first line of the list of workflows, you should see a workflow running that will publish your release to [pypi.org](https://pypi.org/).
13. When the workflow from the previous step has a green checkmark next to it, go to [pypi.org](https://pypi.org/project/wavefront-sdk-python/) and verify that the latest version is published.
