#!/bin/bash

# environment variables
DEBUG_LOGS=$HOME/.appTrackingLogs/application_tracking_logs
ADB_URL_LINUX=https://dl.google.com/android/repository/platform-tools-latest-linux.zip
ADB_URL_MAC=https://dl.google.com/android/repository/platform-tools-latest-darwin.zip
OS_INFO=`uname`
GITHUB_REPO="git@github.com:JanioPG/App-Tracking-Logs.git"

# COLORS
GREEN="\033[0;32m"
BLUE="\033[0;34m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
CLOSE="\033[0m"

# default strings
ARROW="\n${CYAN}==>${CLOSE}"
CONFIG_EMOJI="⚙️"
FINISH_EMOJI="🚀"
ERROR_EMOJI="🚨"
CHECK_EMOJI="✅"
ALERT_EMOJI="⚠️"

function get_OS_info {
    if [[ $OS_INFO == "Linux" ]]; then
        echo -e "${CYAN}Você é um usuário do Linux. Demais!${CLOSE}"
    elif [[ $OS_INFO == "Darwin" ]]; then
        echo -e "${CYAN}Você é um usuário do Mac. Bom estilo!${CLOSE}"
    else
        [[ $OS_INFO == "WindowsNT" ]]
        echo -e "${CYAN}Você é um usuário do Windows. Ferrou!${CLOSE}"
    fi
}


function create_appTrackingLogs_folder {
    echo -e "${CONFIG_EMOJI} ${GREEN} Começando...${CLOSE}"
    if [[ -d $DEBUG_LOGS ]]; then
        echo " O diretório .appTrackingLogs existe!"
    else
        echo " O diretório .appTrackingLogs não existe. Criando diretórios:"
        mkdir -v -p $DEBUG_LOGS
    fi
}


function download_repository {
    echo -e "\n${CONFIG_EMOJI} ${GREEN} Baixando repositório:${CLOSE}"
    if git --version; then
        git clone $GITHUB_REPO $DEBUG_LOGS

        if [[ $? -eq 0 ]]; then
            echo -e "${CYAN}\tFeito: repositório baixado!${CLOSE} ${CHECK_EMOJI}"
            add_alias
        else
            echo -e "\n${CONFIG_EMOJI} ${GREEN} Atualizando repositório...${CLOSE}"
            cd $DEBUG_LOGS && git pull origin main
            if [[ $? -eq 0 ]]; then
                echo -e "${CYAN}\tFeito: Repositório atualizado!${CLOSE} ${CHECK_EMOJI}"
                add_alias
            else
                echo -e "${ERROR_EMOJI} ${RED} Erro ao baixar o repositório. Veja o erro e após corrigir, se necessário, execute novamente o script.${CLOSE}"
            fi
        fi
    else
        echo -e "${ALERT_EMOJI} ${YELLOW} Git não está instalado.${CLOSE}"
        echo " Instale com apt para Linux (debian/ubuntu): 'sudo apt install git'."
        echo " Ou com o homebrew para Mac: 'brew install git'."
        echo " NOTA: Após instalar, adicione seu nome com:"
        echo -e "${YELLOW}\tgit config --global user.name 'seunome'.${CLOSE}"
        echo -e "      Adicione seu e-mail com:"
        echo -e "${YELLOW}\tgit config --global user.email 'example@domain.com'.${CLOSE}"
        echo " Após instalar e configurar o git, execute novamente ./install.sh"
    fi
}


function add_alias {
    echo -e "\n${CONFIG_EMOJI} ${GREEN} Adicionando alias para os scripts.${CLOSE}"

    # zsh
    if grep 'alias\ tracking_android' ~/.zshrc; then
        echo "alias tracking_android existe no arquivo .zshrc."
    else
        echo -ne "\nalias tracking_android=" >> ~/.zshrc
        echo -e \"python3 \`find \$HOME/.appTrackingLogs -iname \'android*logs.py\' -print\`\" >> ~/.zshrc
    fi

    if grep 'alias\ tracking_ios' ~/.zshrc; then
        echo "alias tracking_ios existe no arquivo .zshrc."
    else
        echo -ne "alias tracking_ios=" >> ~/.zshrc
        echo -e \"python3 \`find \$HOME/.appTrackingLogs -iname \'ios*logs.py\' -print\`\" >> ~/.zshrc
    fi
    echo -e "${CYAN}\tConcluído para zsh.${CLOSE} ${CHECK_EMOJI}"

    # bash
    if grep 'alias\ tracking_android' ~/.bashrc; then
        echo "alias tracking_android existe no arquivo .bashrc."
    else
        echo -ne "\nalias tracking_android=" >> ~/.bashrc
        echo -e \"python3 \`find \$HOME/.appTrackingLogs -iname \'android*logs.py\' -print\`\" >> ~/.bashrc
    fi

    if grep 'alias\ tracking_ios' ~/.bashrc; then
        echo "alias tracking_ios existe no arquivo .bashrc."
    else
        echo -ne "alias tracking_ios=" >> ~/.bashrc
        echo -e \"python3 \`find \$HOME/.appTrackingLogs -iname \'ios*logs.py\' -print\`\" >> ~/.bashrc
    fi
    echo -e "${CYAN}\tConcluído para bash.${CLOSE} ${CHECK_EMOJI}"

    install_adb
}


function add_adb_to_path {
    echo -e "\n${CONFIG_EMOJI} ${GREEN} Adicionando 'adb' à variável path:${CLOSE}"

    if ! grep 'export\ PATH.*platform-tools' ~/.zshrc; then
        echo -e "\n# Adicionando adb na variável path" >> ~/.zshrc
        echo -e "export PATH=\$PATH:\$HOME/.appTrackingLogs/platform-tools" >> ~/.zshrc
    fi
    echo -e "${CYAN}\tConcluído para zsh.${CLOSE} ${CHECK_EMOJI}"

    if ! grep 'export\ PATH.*platform-tools' ~/.bashrc; then
        echo -e "\n# Adicionando adb na variável path" >> ~/.bashrc
        echo -e "export PATH=\$PATH:\$HOME/.appTrackingLogs/platform-tools" >> ~/.bashrc
    fi
    echo -e "${CYAN}\tConcluído para bash.${CLOSE} ${CHECK_EMOJI}"
}


function download_adb {

    get_OS_info

    if [[ $OS_INFO == "01Linux" ]]; then
        curl $ADB_URL_LINUX -# -L --create-dirs -o $HOME/.appTrackingLogs/platform-tools.zip -C -
    elif [[ $OS_INFO == "01Darwin" ]]; then
        curl $ADB_URL_MAC -# -L --create-dirs -o $HOME/.appTrackingLogs/platform-tools.zip -C -
    else
        echo "${ERROR_EMOJI} Você não é usuário Linux e nem Mac. Mas baixe o adb para seu sistema operacional em 'https://developer.android.com/studio/releases/platform-tools'."
        exit 1
    fi

    if [[ $? -eq 0 ]]; then
        echo -e "\n${CONFIG_EMOJI} adb baixado com sucesso. ${CHECK_EMOJI} \nDescompactando:"
        cd $HOME/.appTrackingLogs && unzip platform-tools.zip

        add_adb_to_path

    else
        echo "${ALERT_EMOJI} Erro ao baixar o adb. Veja o erro e tente executar novamente o script."
        echo "Se for o erro '92', talvez seja porque você já tem o arquivo do adb baixado na pasta .appTrackingLogs."
    fi
}


function install_adb {
    echo -e "\n${CONFIG_EMOJI} ${GREEN} Verificando se o 'adb' está instalado (aplicável para Android):${CLOSE}"
    if ! adb --version; then
        echo -e "${ALERT_EMOJI} ${YELLOW} O 'adb' não foi encontrado.${CLOSE}"
        echo "Nota: Se você instalou o Android Studio, talvez precise adicionar o adb à variável path ou adicionar um alias."

        if [[ $OS_INFO == "Darwin" ]]; then
            if find ~/Library/Android/sdk/platform-tools -iname adb -print; then
                echo -e "${YELLOW}Apesar disso, encontrei o adb em ~/Library/Android/sdk/platform-tools/adb. Adicione-o à variável path para usar.${CLOSE}"
                echo "Em seu arquivo .zshrc (ou .bashrc) na home, adicione a linha:"
                echo -e "\texport PATH=\$PATH:\$HOME/Library/Android/sdk/platform-tools"
            fi
        elif [[ $OS_INFO == "Linux" ]]; then
            if ls `find ~/Android -type d -iname platform-tools -print` | grep adb; then
                echo -e "${YELLOW}Apesar disso, encontrei o adb em ~/Android/Sdk/platform-tools/adb. Adicione-o à variável path para utilizá-lo.${CLOSE}"
                echo "Em seu arquivo .zshrc (ou .bashrc) localizado na home, adicione a linha:"
                echo -e "\texport PATH=\$PATH:\$HOME/Android/platform-tools"
            fi
        fi

        while true; do
        read -n1 -p "Deseja instalar o adb? [Y/n]: " userResponse
            case $userResponse in
                Y | y) echo
                    echo -e "${CYAN}Você escolheu instalar.${CLOSE}"

                    download_adb

                    break;;
                N | n) echo
                    break;;
                *) echo
                    echo -e "${ERROR_EMOJI} ${RED}Opção inválida. Digite somente y (yes) ou n (no).${CLOSE}";;
            esac
        done
    fi

    completion_message
}


function completion_message {
    echo -e "\n${FINISH_EMOJI} ${GREEN}Concluído!${CLOSE}"
    echo "Reincie o terminal (fechando e abrindo novamente) para que as configurações do shell sejam recarregadas."
    echo -e "Recarregadas as configurações, execute no seu terminal ${CYAN}'tracking_android'${CLOSE} para ver os eventos de Android ou ${CYAN}'tracking_ios'${CLOSE} para ver os eventos de iOS.\n\nEm caso de dúvidas, contate: guild mobile solutions ou janio.garcia@mediamonks.com"
}

create_appTrackingLogs_folder
download_repository
