# Application Tracking Logs

### Feature: apresentar logs relacionados ao app tracking de forma mais amigável. Ao executar, veja uma das opções como Google Analytics 4, AppsFlyer e Google Tag Manager.

![Debug Logs](https://drive.google.com/uc?id=19eu2Ah2aoBhBIMZOsYHeNNd3wkm1FTFG)

---
## **Dependências**:

* [Python 3.10+](https://www.python.org/)
* [Android Debug Bridge (adb)](https://developer.android.com/studio/command-line/adb)

## **Como utilizar**:

Após clonar o repositório, ainda no terminal, mude seu diretório para a raiz do projeto.
Uma vez na raiz do projeto, você pode executar o script de acordo com o sistema operacional do seu app.
Inicialize seu emulador Android ou iOS Simulator. Caso esteja utilizando um dispositivo físico (Android), apenas certifique-se que o mesmo esteja em modo debug e conectado à sua máquina.

Android:
`python android_debug_logs.py` ou `python3 android_debug_logs.py`

iOS:
`python ios_debug_logs.py` ou `python3 ios_debug_logs.py`

Após executar o script, verá um menu opções de plataforma.

---
## **Instalação alternativa [Optional]**:

Baixe o arquivo _install.sh_.

Conceda permissão de execução para o arquivo (shell script) com o comando: `chmod +x install.sh`

Em seguida, execute com o comando: `./install.sh`

Assim que finalizado, você pode simplesmente executar o script de qualquer diretório com os comandos:

Android: `tracking_android`

iOS: `tracking_ios`

#### Função secundária: Filtro

Execute no seu terminal: `python android_debug_logs.py -p1 <filtro_1> -p2 <filtro_2>` ou `python ios_debug_logs.py -p1 <filtro_1> -p2 <filtro_2>`

Exemplo:

Obtenha, para GA4, somente o registro do evento add_to_cart e destaque o parâmetro value:

` python android_debug_logs.py -p1 "add_to_cart" -p2 "value"`

Veja somente o registro do evento purchase (android e iOS):

` python android_debug_logs.py -p1 "name=purchase|purchase"`
