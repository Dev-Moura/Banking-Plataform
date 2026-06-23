from time import sleep
from typing import List

from models.cliente import Cliente
from models.conta import Conta

contas: List[Conta] = []


def main() -> None:
    menu()


def criar_conta() -> None:
    print("Informe os dados para criar uma conta:")

    nome: str = input("Nome: ")
    email: str = input("Email: ")
    cpf: str = input("CPF: ")
    data_nascimento: str = input("Data de nascimento: ")

    cliente: Cliente = Cliente(nome, email, cpf, data_nascimento)

    conta: Conta = Conta(cliente)

    contas.append(conta)

    print("Conta criada com sucesso")
    print("Dados da conta:")
    print("-----------------")
    print(conta)
    print(f"Saldo: {conta.saldo}")
    sleep(2)
    menu()


def efetuar_deposito() -> None:
    if len(contas) > 0:
        numero: int = int(input("Número da conta: "))

        conta: Conta = buscar_conta_por_numero(numero)

        if conta:
            valor: float = float(input("Informe o valor do depoósito: "))

            conta.depositar(valor)
        else:
            print(f"Não foi possível encontrar a conta com número {numero}")
        sleep(2)
        menu()
    else:
        print("Não há contas para efetuar o depósito")
        sleep(2)
        menu()


def efetuar_saque() -> None:
    if len(contas) > 0:
        numero: int = int(input("Número da conta: "))

        conta: Conta = buscar_conta_por_numero(numero)

        if conta:
            valor: float = float(input("Informe o valor: "))

            conta.sacar(valor)
        else:
            print(f"Não foi encontrar a conta com número {numero}")
    else:
        print("Não há contas para efetuar o saque")
        sleep(2)
        menu()


def efetuar_transferencia() -> None:
    if len(contas) > 0:
        numero_origem: int = int(input("Número da conta sua conta "))

        conta_origem: Conta = buscar_conta_por_numero(numero_origem)

        if conta_origem:
            numero_destino: int = int(input("Informe o número da conta destino: "))

            conta_destino: Conta = buscar_conta_por_numero(numero_destino)

            if conta_destino:
                valor: float = float(input("Informe o valor: "))
                conta_origem.transferir(conta_destino, valor)

            else:
                print(f"Não foi possível encontrar a conta com número {numero_destino}")
        else:
            print(f"Não foi possível encontrar a conta com número {numero_origem}")
    else:
        print("Não há contas para efetuar a transferência")
    sleep(2)
    menu()


def listar_contas() -> None:
    if len(contas) > 0:
        print("listagem de contas")

        for conta in contas:
            print(conta)
            print("-----------//-------------")
            sleep(1)
    else:
        print("Não há contas para listar")
    sleep(2)
    menu()


def buscar_conta_por_numero(numero: int) -> Conta:
    c: Conta | None = None

    if len(contas) > 0:
        for conta in contas:
            if conta.numero == numero:
                c = conta
    return c


def menu() -> None:
    print("==========================================")
    print("================== ATM ===================")
    print("=============== GEEK BANK ================")
    print("==========================================")

    print("Selecione uma opção no menu: ")
    print("1 - Criar conta: ")
    print("2 - Efetuar saque:  ")
    print("3 - Efetuar depósito: ")
    print("4 - Efetuar transferência: ")
    print("5 - Listar contas: ")
    print("0 - Sair")

    opcao: int = int(input())

    match opcao:
        case 1:
            criar_conta()
        case 2:
            efetuar_saque()
        case 3:
            efetuar_deposito()
        case 4:
            efetuar_transferencia()
        case 5:
            listar_contas()
        case 0:
            print("Volte Sempre")
            sleep(2)
            exit(0)
        case _:
            print("Opção inválida!")
            sleep(2)
            menu()


if __name__ == "__main__":
    main()
