pipeline {
    agent {
        kubernetes {
          //cloud 'kubernetes'
          defaultContainer 'openjdk'
          yaml '''
            kind: Pod
            spec:
              containers:
              - name: openjdk
                image: openjdk:latest
                imagePullPolicy: Always
                command:
                - sleep
                args:
                - 99d
    '''
        }
    }

    stages {
        stage('Hello') {
            steps {
                echo 'Hello World'
            }
        }
        // 这里的hello2 是我加的，就是说明，这是stages下的第二个任务 ,就是在pipeline中加单行注释 用 // 就行
        stage('Hello2') {
            steps {
                sh '''echo \'Hello World，i 应该是 可以了 -2 ！！！\'
                ls -a /home/jenkins/agent/workspace'''
            }
        }

//         stage('SCM') {
//             steps {
//                 git 'https://github.com/san5167/MyTestRepository.git'
//             }
//         }
        
        stage('SonarQube analysis') {
            steps {
                script {
                    def scannerHome = tool 'sonar-devops';
                    withSonarQubeEnv('sonarqube-scanner') { // If you have configured more than one global server connection, you can specify its name
                        sh "pwd";
                        sh "ls";
                  
                        sh "ls ${scannerHome}";
                        sh "cat ${scannerHome}/bin/sonar-scanner";
                        sh "${scannerHome}/bin/sonar-scanner -X -Dsonar.projectKey=serviceSet";
                    }
                }
            }
        }
        
        
        //前
        stage('sonar load result'){
            steps{
                script{
                        timeout(time: 1, unit: 'HOURS') { // Just in case something goes wrong, pipeline will be killed after a timeout
                            def qg = waitForQualityGate() // Reuse taskId previously collected by withSonarQubeEnv
                            if (qg.status != 'OK') {
                                error "Pipeline aborted due to quality gate failure: ${qg.status},${qg}"
                            }
                            
                        }
                }
            }
        }
        
        //后
        
    }
}
