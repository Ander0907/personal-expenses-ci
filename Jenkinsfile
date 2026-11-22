// Declarative pipeline for personal-expenses-ci (Jenkins running in a container
// with the host Docker socket mounted; see jenkins/).
//
// Jenkins configuration this file relies on (never stored in the repo):
//   - SCM credentials ("github-pat", Username with password) set on the job.
//   - Secret file credential "expenses-env-file" with the contents of .env.
//   - The Jenkins container must be named "jenkins" (the pipeline runs
//     `docker network connect ... jenkins` and .inside uses --volumes-from it).
//   - pollSCM below is registered only after the first (manual) build.

// Copies the Secret file credential to .env in the workspace. docker compose
// reads env_file on the client side, so .env must exist before ANY compose call.
// The content is never printed; .env is removed in post { always }.
def prepareEnv() {
    withCredentials([file(credentialsId: 'expenses-env-file', variable: 'ENV_FILE')]) {
        sh 'umask 077; cp "$ENV_FILE" .env'
    }
}

pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        // Compose project, network, volume and port have fixed names.
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        // The Checkout stage does it explicitly.
        skipDefaultCheckout()
    }

    // A local Jenkins is not reachable from GitHub, so poll instead of webhooks.
    triggers {
        pollSCM('H/2 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                // Repository URL, branch and credentials come from the job's SCM config.
                checkout scm
            }
        }

        stage('Lint & Unit Test') {
            agent {
                docker {
                    image 'python:3.12.16-slim-bookworm'
                    reuseNode true
                    // uid 1000 has no writable HOME in this image.
                    // No credentials are passed: .inside mounts jenkins_home
                    // (--volumes-from), so this container must stay secret-free.
                    args '-e HOME=/tmp'
                }
            }
            steps {
                dir('api') {
                    // The venv lives outside the workspace, so it never reaches the build context.
                    sh '''
                        python -m venv /tmp/venv
                        . /tmp/venv/bin/activate
                        pip install --quiet -r requirements-dev.txt -c constraints.txt
                        ruff check .
                        ruff format --check .
                        # Coverage gate (--cov-fail-under=90) is part of pyproject addopts.
                        pytest
                    '''
                }
            }
        }

        stage('Build') {
            steps {
                // Compose project, network and volume use fixed names shared with a local
                // checkout. Refuse to run (and to clean up!) if a local stack or its data exists.
                sh '''
                    if docker volume inspect expenses-db-data >/dev/null 2>&1 ||
                       [ -n "$(docker ps -aq --filter label=com.docker.compose.project=personal-expenses)" ]; then
                        echo "A local personal-expenses stack/volume exists: run 'docker compose down -v' in your local checkout before building (this pipeline uses the same fixed names)."
                        exit 1
                    fi
                '''
                // Only past the guard does this build own the stack; post { always } relies on it.
                script { env.STACK_OWNED = 'true' }
                prepareEnv()
                // api is built from ./api; db is the official image (no Dockerfile of its own).
                sh '''
                    docker compose build api
                    docker compose pull db
                '''
            }
        }

        stage('Integration Test') {
            steps {
                // --no-build: fails clearly if the image built above is not the one compose uses.
                sh 'docker compose up -d --wait --no-build --wait-timeout 120'
                sh 'docker compose ps'
                // Put Jenkins on the compose network so it can reach the API by service name.
                sh 'docker network disconnect expenses-net jenkins >/dev/null 2>&1 || true'
                sh 'docker network connect expenses-net jenkins'
                // Visible proof that the API resolves the database by service name.
                sh '''
                    docker compose exec -T api getent hosts db
                    docker compose exec -T api printenv DATABASE_HOST
                '''
                // Any failed check makes the script (and the build) fail.
                withEnv(['BASE_URL=http://api:8000']) {
                    sh 'bash scripts/smoke_test.sh'
                }
            }
        }
    }

    post {
        failure {
            echo 'Build FAILED: see the container logs above.'
        }
        success {
            echo 'Build OK: images built and the API talks to the database by service name.'
        }
        // Declarative runs "always" BEFORE "failure"/"success", so logs and cleanup
        // live here in the right order: logs, disconnect, down, remove .env.
        always {
            script {
                // Compose commands only run if THIS build created the stack (flag set after the
                // guard in Build); otherwise `down -v` could destroy the user's local data.
                if (env.STACK_OWNED == 'true') {
                    try {
                        // down needs .env: the build may have failed before it was created.
                        if (!fileExists('.env')) {
                            prepareEnv()
                        }
                        if (currentBuild.currentResult != 'SUCCESS') {
                            sh 'docker compose logs --no-color --tail=200 || true'
                        }
                    } catch (err) {
                        echo 'Could not prepare .env in post; continuing with cleanup.'
                    }
                }
            }
            // Disconnect first, otherwise Jenkins keeps expenses-net in use and it cannot be removed.
            sh 'docker network disconnect expenses-net jenkins >/dev/null 2>&1 || true'
            script {
                if (env.STACK_OWNED == 'true') {
                    sh 'docker compose down -v || true'
                }
            }
            sh 'rm -f .env'
        }
    }
}
