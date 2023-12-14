from invoke import task


@task()
def function_debug(c):
    c.run("functions-framework --target=hello_world --debug")


@task()
def gcloud_deploy(c):
    c.run(
        """gcloud functions deploy python-http-function --gen2 --runtime=python312 \
          --region=europe-west3 --source=. --entry-point=hello_world --trigger-http"""
    )


@task()
def pip_create_venv(c, venv_name):
    c.run(f"python -m venv {venv_name}_venv")
    c.run(f"{venv_name}_venv/bin/pip install -r requirements_{venv_name}.txt")


@task()
def pip_freeze_venv(c, venv_name):
    c.run(f"{venv_name}_venv/bin/pip freeze > requirements_{venv_name}.txt")


@task()
def pip_prepare_venvs(c, remove_venvs=False):
    if remove_venvs:
        c.run("rm -r *_venv", pty=True)
    pip_create_venv(c, "sync")


@task()
def pip_freeze(c):
    pip_freeze_venv(c, "sync")


@task
def dk_save(c):
    c.run("docker save --output google_sync.tar google_sync-google_sync")


@task
def dk_load(c):
    c.run("docker load --input google_sync.tar")


@task(dk_save)
def dk_copy(c):
    c.run("scp tasks.py hetzner5:jbeelte/google_sync")
    c.run(
        "scp docker-compose-deploy.yml hetzner5:jbeelte/google_sync/docker-compose.yml"
    )
    c.run("scp google_sync.tar hetzner5:jbeelte/google_sync")
