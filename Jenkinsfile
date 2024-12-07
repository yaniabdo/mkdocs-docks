pipeline {
    agent any
    
    stages {
        stage('Generate Documentation') {
            steps {
                sh '''
                    cd /home/ec2-user/mkdocs-vpc
                    python3 scripts/vpc_docs_generator.py
                '''
            }
        }
        
        stage('Build and Deploy') {
            steps {
                sh '''
                    cd /home/ec2-user/mkdocs-vpc
                    mkdocs build
                    sudo cp -r site/* /var/www/html/site/
                    sudo chown -R nginx:nginx /var/www/html/site
                '''
            }
        }
    }
}
