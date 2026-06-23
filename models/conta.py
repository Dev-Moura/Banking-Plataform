from models.cliente import Cliente
from utils import formatar_flaot_str_moeda


class Conta:
    codigo: int = 1001

    def __init__(self, cliente: Cliente) -> None:
        self.__numero: int = Conta.codigo
        self.__cliente: Cliente = cliente
        self.__saldo: float = 0.0
        self.__limite: float = 0.0
        self.__saldo_total: float = self._calcula_saldo_total
        Conta.codigo += 1

    def __str__(self) -> str:
        return (
            f"Número da conta: {self.__numero} \nCliente: {self.__cliente.nome}"
            f"\nSaldo Total: {formatar_flaot_str_moeda(self.__saldo_total)}"
        )

    @property
    def numero(self) -> int:
        return self.__numero

    @property
    def cliente(self) -> Cliente:
        return self.__cliente

    @property
    def saldo(self) -> float:
        return self.__saldo

    @saldo.setter
    def saldo(self, valor: float) -> None:
        self.__saldo = valor

    @property
    def limite(self) -> float:
        return self.__saldo

    @limite.setter
    def limite(self, valor: float) -> None:
        self.__limite = valor

    @property
    def saldo_total(self) -> float:
        return self.__saldo_total

    @saldo_total.setter
    def saldo_total(self, valor: float) -> None:
        self.__saldo_total = valor

    @property
    def _calcula_saldo_total(self) -> float:
        return self.saldo + self.limite

    def depositar(self, valor: float) -> None:
        if valor > 0:
            self.saldo += valor
            self.saldo_total = self._calcula_saldo_total
            print("Depósito efetuado com sucesso! ")
        else:
            print("Erro ao efetuar depósito. Tente novamente")

    def sacar(self, valor: float) -> None:
        if valor > 0 and self.saldo >= valor:
            if self.saldo >= valor:
                self.saldo -= valor
                self.saldo_total = self._calcula_saldo_total
            else:
                restante: float = self.saldo - valor
                self.limite = self.limite + restante
                self.saldo = 0
                self.saldo_total = self._calcula_saldo_total
        else:
            print("Saque não realizado. Tente Novamente")

    def transferir(self, destino: "Conta", valor: float) -> None:
        if valor > 0 and self.saldo_total >= valor:
            if self.saldo >= valor:
                self.saldo -= valor
                self.saldo_total = self._calcula_saldo_total
                destino.saldo += valor
                destino.saldo_total = destino._calcula_saldo_total
            else:
                restante: float = self.saldo - valor
                self.saldo = 0
                self.limite += restante
                self.saldo_total = self._calcula_saldo_total
                destino.saldo += valor
                destino.saldo_total = destino._calcula_saldo_total
            print("Transferência realizada com sucesso.")
        else:
            print("Transferência não realizada. Tente Novamente")
