"""
===============================================================================
SISTEMA DE GESTÃO CONDOMINIAL
===============================================================================
Documentação Simplificada:
Este sistema gerencia moradores e unidades (apartamentos) de um condomínio.
Utiliza Programação Orientada a Objetos, persistência em arquivos JSON/TXT/CSV,
consumo de API pública (ViaCEP) para validação de endereços, tratamento de 
exceções personalizadas, geração de relatórios gerenciais, logs e backups.
===============================================================================
"""

import json
import csv
import os
from datetime import datetime
import urllib.request
import urllib.error

# =============================================================================
# EXCEÇÕES PERSONALIZADAS
# =============================================================================
class RegistroDuplicado(Exception):
    """Exceção acionada quando tenta-se cadastrar um registro já existente."""
    pass

class ArquivoInexistente(Exception):
    """Exceção acionada quando um arquivo necessário não é encontrado."""
    pass

class ApiIndisponivel(Exception):
    """Exceção acionada quando há falha na comunicação com a API externa."""
    pass

class DadosInvalidos(Exception):
    """Exceção acionada quando dados fornecidos estão incorretos ou vazios."""
    pass

# =============================================================================
# PROGRAMAÇÃO ORIENTADA A OBJETOS (3 Classes com Construtores)
# =============================================================================
class Morador:
    """Classe que representa um morador do condomínio."""
    def __init__(self, nome, cpf, telefone, email):
        self.nome = nome
        self.cpf = cpf
        self.telefone = telefone
        self.email = email

    def to_dict(self):
        return {
            "nome": self.nome,
            "cpf": self.cpf,
            "telefone": self.telefone,
            "email": self.email
        }


class Apartamento:
    """Classe que representa uma unidade (apartamento) no condomínio."""
    def __init__(self, numero, bloco, morador_responsavel, cep=""):
        self.numero = numero
        self.bloco = bloco
        self.morador_responsavel = morador_responsavel
        self.cep = cep
        self.endereco_api = ""

    def to_dict(self):
        return {
            "numero": self.numero,
            "bloco": self.bloco,
            "morador_responsavel": self.morador_responsavel,
            "cep": self.cep,
            "endereco_api": self.endereco_api
        }


class SistemaGestao:
    """Classe principal que gerencia as regras de negócio, arquivos, API e CRUD."""
    def __init__(self, arquivo_dados="dados_condominio.json"):
        self.arquivo_dados = arquivo_dados
        self.dados = {"moradores": [], "apartamentos": []}
        self.carregar_dados()
        self.criar_backup()

    # --- PERSISTÊNCIA E MANIPULAÇÃO DE ARQUIVOS ---
    def carregar_dados(self):
        """Lê os dados do arquivo JSON de persistência."""
        try:
            if os.path.exists(self.arquivo_dados):
                with open(self.arquivo_dados, "r", encoding="utf-8") as f:
                    self.dados = json.load(f)
                self.registrar_log("Dados carregados com sucesso.")
            else:
                self.salvar_dados() # Cria arquivo vazio se não existir
        except Exception as e:
            self.registrar_log(f"Erro ao carregar dados: {e}")
            raise ArquivoInexistente(f"Não foi possível ler o arquivo de dados: {e}")

    def salvar_dados(self):
        """Escreve/persiste os dados no arquivo JSON."""
        try:
            with open(self.arquivo_dados, "w", encoding="utf-8") as f:
                json.dump(self.dados, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.registrar_log(f"Erro ao salvar dados: {e}")
            raise DadosInvalidos(f"Erro ao salvar arquivo de persistência: {e}")

    # --- CONSUMO DE API (ViaCEP) ---
    def consultar_cep_api(self, cep):
        """Consome a API ViaCEP para buscar dados de endereço através do CEP."""
        cep_limpo = "".join(filter(str.isdigit, cep))
        if len(cep_limpo) != 8:
            raise DadosInvalidos("CEP inválido. Deve conter 8 dígitos.")
        
        url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                resposta_data = json.loads(response.read().decode('utf-8'))
                if "erro" in resposta_data:
                    raise DadosInvalidos("CEP não encontrado na base de dados.")
                endereco = f"{resposta_data.get('logradouro', '')}, {resposta_data.get('bairro', '')} - {resposta_data.get('localidade', '')}/{resposta_data.get('uf', '')}"
                return endereco
        except urllib.error.URLError:
            raise ApiIndisponivel("Serviço de consulta de CEP indisponível no momento.")
        except Exception as e:
            raise ApiIndisponivel(f"Erro na conexão com a API: {e}")

    # --- FUNCIONALIDADES ADICIONAIS ---
    def registrar_log(self, mensagem):
        """Recurso Adicional: Sistema de Logs em arquivo TXT."""
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("sistema.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"[{data_hora}] {mensagem}\n")

    def criar_backup(self):
        """Recurso Adicional: Backup Automático dos Dados."""
        if os.path.exists(self.arquivo_dados):
            with open(self.arquivo_dados, "r", encoding="utf-8") as original:
                conteudo = original.read()
            with open("backup_condominio.json", "w", encoding="utf-8") as backup:
                backup.write(conteudo)

    # --- CRUD (Cadastro, Consulta, Atualização, Exclusão) ---
    def cadastrar(self):
        print("\n--- CADASTRO DE REGISTROS ---")
        print("1. Cadastrar Morador")
        print("2. Cadastrar Apartamento")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            nome = input("Nome do Morador: ").strip()
            cpf = input("CPF (apenas números): ").strip()
            telefone = input("Telefone: ").strip()
            email = input("E-mail: ").strip()

            if not nome or not cpf:
                raise DadosInvalidos("Nome e CPF são obrigatórios.")

            # Verifica duplicidade
            for m in self.dados["moradores"]:
                if m["cpf"] == cpf:
                    raise RegistroDuplicado(f"Já existe um morador cadastrado com o CPF {cpf}.")

            novo_morador = Morador(nome, cpf, telefone, email)
            self.dados["moradores"].append(novo_morador.to_dict())
            self.salvar_dados()
            self.registrar_log(f"Morador {nome} cadastrado com sucesso.")
            print("✅ Morador cadastrado com sucesso!")

        elif opcao == "2":
            numero = input("Número do Apartamento: ").strip()
            bloco = input("Bloco: ").strip()
            morador_resp = input("Nome do Morador Responsável: ").strip()
            cep = input("CEP da Correspondência/Unidade (opcional): ").strip()

            # Validação e Consulta de API
            endereco_encontrado = ""
            if cep:
                try:
                    endereco_encontrado = self.consultar_cep_api(cep)
                    print(                    f"📍 Endereço localizado via API: {endereco_encontrado}")
                except (ApiIndisponivel, DadosInvalidos) as e:
                    print(f"⚠️ Aviso de API: {e}. Prosseguindo sem endereço automático.")

            # Verifica duplicidade
            for ap in self.dados["apartamentos"]:
                if ap["numero"] == numero and ap["bloco"] == bloco:
                    raise RegistroDuplicado(f"O apartamento {numero} Bloco {bloco} já está cadastrado.")

            novo_ap = Apartamento(numero, bloco, morador_resp, cep)
            novo_ap.endereco_api = endereco_encontrado
            self.dados["apartamentos"].append(novo_ap.to_dict())
            self.salvar_dados()
            self.registrar_log(f"Apartamento {numero}/{bloco} cadastrado.")
            print("✅ Apartamento cadastrado com sucesso!")
        else:
            raise DadosInvalidos("Opção de cadastro inválida.")

    def consultar(self):
        print("\n--- CONSULTA DE REGISTROS ---")
        print("1. Listar Moradores")
        print("2. Listar Apartamentos")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            if not self.dados["moradores"]:
                print("Nenhum morador cadastrado.")
                return
            print("\n--- LISTA DE MORADORES ---")
            for m in self.dados["moradores"]:
                print(f"Nome: {m['nome']} | CPF: {m['cpf']} | Tel: {m['telefone']} | E-mail: {m['email']}")
        elif opcao == "2":
            if not self.dados["apartamentos"]:
                print("Nenhum apartamento cadastrado.")
                return
            print("\n--- LISTA DE APARTAMENTOS ---")
            for ap in self.dados["apartamentos"]:
                end_str = f" | Endereço: {ap['endereco_api']}" if ap['endereco_api'] else ""
                print(f"Apto: {ap['numero']} - Bloco: {ap['bloco']} | Responsável: {ap['morador_responsavel']}{end_str}")
        else:
            raise DadosInvalidos("Opção de consulta inválida.")

    def alterar(self):
        print("\n--- ALTERAÇÃO DE REGISTROS ---")
        print("1. Alterar Morador")
        print("2. Alterar Apartamento")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            cpf = input("Informe o CPF do morador que deseja alterar: ").strip()
            encontrado = False
            for m in self.dados["moradores"]:
                if m["cpf"] == cpf:
                    encontrado = True
                    print(f"Encontrado: {m['nome']}. Digite os novos dados (deixe em branco para manter):")
                    novo_nome = input(f"Novo nome [{m['nome']}]: ").strip()
                    novo_tel = input(f"Novo telefone [{m['telefone']}]: ").strip()
                    novo_email = input(f"Novo e-mail [{m['email']}]: ").strip()

                    if novo_nome: m['nome'] = novo_nome
                    if novo_tel: m['telefone'] = novo_tel
                    if novo_email: m['email'] = novo_email
                    
                    self.salvar_dados()
                    self.registrar_log(f"Morador com CPF {cpf} atualizado.")
                    print("✅ Dados do morador atualizados com sucesso!")
                    break
            if not encontrado:
                raise ArquivoInexistente("Morador não encontrado com o CPF informado.")

        elif opcao == "2":
            numero = input("Número do apartamento: ").strip()
            bloco = input("Bloco: ").strip()
            encontrado = False
            for ap in self.dados["apartamentos"]:
                if ap["numero"] == numero and ap["bloco"] == bloco:
                    encontrado = True
                    novo_resp = input(f"Novo morador responsável [{ap['morador_responsavel']}]: ").strip()
                    if novo_resp: ap['morador_responsavel'] = novo_resp
                    self.salvar_dados()
                    self.registrar_log(f"Apartamento {numero}/{bloco} atualizado.")
                    print("✅ Dados do apartamento atualizados com sucesso!")
                    break
            if not encontrado:
                raise ArquivoInexistente("Apartamento não encontrado.")
        else:
            raise DadosInvalidos("Opção inválida.")

    def excluir(self):
        print("\n--- EXCLUSÃO DE REGISTROS ---")
        print("1. Excluir Morador")
        print("2. Excluir Apartamento")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            cpf = input("Informe o CPF do morador a ser excluído: ").strip()
            tamanho_inicial = len(self.dados["moradores"])
            self.dados["moradores"] = [m for m in self.dados["moradores"] if m["cpf"] != cpf]
            if len(self.dados["moradores"]) < tamanho_inicial:
                self.salvar_dados()
                self.registrar_log(f"Morador CPF {cpf} excluído.")
                print("🗑️ Morador excluído com sucesso!")
            else:
                raise ArquivoInexistente("Morador com este CPF não foi encontrado.")

        elif opcao == "2":
            numero = input("Número do apartamento: ").strip()
            bloco = input("Bloco: ").strip()
            tamanho_inicial = len(self.dados["apartamentos"])
            self.dados["apartamentos"] = [ap for ap in self.dados["apartamentos"] if not (ap["numero"] == numero and ap["bloco"] == bloco)]
            if len(self.dados["apartamentos"]) < tamanho_inicial:
                self.salvar_dados()
                self.registrar_log(f"Apartamento {numero}/{bloco} excluído.")
                print("🗑️ Apartamento excluído com sucesso!")
            else:
                raise ArquivoInexistente("Apartamento não encontrado.")
        else:
            raise DadosInvalidos("Opção inválida.")

    # --- RELATÓRIOS E EXPORTAÇÃO ---
    def gerar_relatorio(self):
        """Gera um relatório gerencial completo salvo em arquivo TXT."""
        nome_arquivo = "relatorio_gerencial_condominio.txt"
        try:
            with open(nome_arquivo, "w", encoding="utf-8") as rel:
                rel.write("="*50 + "\n")
                rel.write("       RELATÓRIO GERENCIAL - SISTEMA CONDOMINIAL\n")
                rel.write(f"       Data de Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                rel.write("="*50 + "\n\n")
                
                rel.write(f"Total de Moradores Cadastrados: {len(self.dados['moradores'])}\n")
                rel.write(f"Total de Apartamentos Cadastrados: {len(self.dados['apartamentos'])}\n\n")
                
                rel.write("--- RELAÇÃO DE MORADORES ---\n")
                for m in self.dados["moradores"]:
                    rel.write(f"- Nome: {m['nome']} | CPF: {m['cpf']} | Tel: {m['telefone']}\n")
                
                rel.write("\n--- RELAÇÃO DE APARTAMENTOS ---\n")
                for ap in self.dados["apartamentos"]:
                    rel.write(f"- Apto {ap['numero']}, Bloco {ap['bloco']} | Responsável: {ap['morador_responsavel']}\n")
                
                rel.write("\n" + "="*50 + "\nFIM DO RELATÓRIO\n")
            
            self.registrar_log("Relatório gerencial gerado com sucesso (TXT).")
            print(f"📊 Relatório gerencial gerado e salvo com sucesso no arquivo '{nome_arquivo}'!")
        except Exception as e:
            raise DadosInvalidos(f"Erro ao gerar relatório: {e}")

    def exportar_dados(self):
        """Recurso Adicional: Exportação de dados para CSV e JSON."""
        print("\n--- EXPORTAR DADOS ---")
        print("1. Exportar para CSV (Apartamentos)")
        print("2. Exportar cópia para JSON")
        opcao = input("Escolha o formato: ")

        if opcao == "1":
            nome_csv = "apartamentos_exportados.csv"
            with open(nome_csv, mode="w", newline="", encoding="utf-8") as f:
                escritor = csv.writer(f)
                escritor.writerow(["Numero", "Bloco", "Responsavel", "CEP", "Endereco"])
                for ap in self.dados["apartamentos"]:
                    escritor.writerow([ap["numero"], ap["bloco"], ap["morador_responsavel"], ap["cep"], ap["endereco_api"]])
            self.registrar_log("Dados exportados para CSV.")
            print(f"📁 Dados exportados com sucesso para '{nome_csv}'!")
        elif opcao == "2":
            nome_json = "backup_exportacao.json"
            with open(nome_json, "w", encoding="utf-8") as f:
                json.dump(self.dados, f, ensure_ascii=False, indent=4)
            self.registrar_log("Dados exportados para JSON.")
            print(f"📁 Cópia JSON exportada com sucesso para '{nome_json}'!")
        else:
            raise DadosInvalidos("Formato de exportação inválido.")


# =============================================================================
# MENU INTERATIVO PRINCIPAL
# =============================================================================
def main():
    try:
        sistema = SistemaGestao()
    except Exception as e:
        print(f"Erro crítico ao iniciar o sistema: {e}")
        return

    while True:
        print("\n========================================")
        print("          SISTEMA CONDOMINIAL           ")
        print("========================================")
        print("1 - Cadastrar")
        print("2 - Consultar")
        print("3 - Alterar")
        print("4 - Excluir")
        print("5 - Gerar Relatório")
        print("6 - Exportar Dados")
        print("7 - Sair")
        print("========================================")
        
        opcao = input("Escolha uma opção (1-7): ").strip()

        try:
            if opcao == "1":
                sistema.cadastrar()
            elif opcao == "2":
                sistema.consultar()
            elif opcao == "3":
                sistema.alterar()
            elif opcao == "4":
                sistema.excluir()
            elif opcao == "5":
                sistema.gerar_relatorio()
            elif opcao == "6":
                sistema.exportar_dados()
            elif opcao == "7":
                print("\nEncerrando o Sistema de Gestão Condominial. Até logo!")
                sistema.registrar_log("Sistema encerrado pelo usuário.")
                break
            else:
                raise DadosInvalidos("Opção inválida! Escolha um número de 1 a 7.")

        # Tratamento Robusto de Exceções Personalizadas e Gerais
        except (RegistroDuplicado, ArquivoInexistente, ApiIndisponivel, DadosInvalidos) as erro:
            print(f"\n❌ [ERRO DE NEGÓCIO]: {erro}")
            sistema.registrar_log(f"Erro tratado: {type(erro).__name__} - {erro}")
        except ValueError as ve:
            print(f"\n❌ [ERRO DE VALOR]: Entrada inválida. {ve}")
        except Exception as ex:
            print(f"\n❌ [ERRO INESPERADO]: {ex}")
            sistema.registrar_log(f"Erro inesperado: {ex}")

if __name__ == "__main__":
    main()