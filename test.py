from models.conta import Conta

from models.cliente import Cliente

michael = Cliente("Michael", "michael@example.com", "123.456.789-00", "01/01/1990")
roberto = Cliente("Roberto", "roberto@example.com", "987.654.321-00", "01/01/1990")

conta_michael: Conta = Conta(michael)
conta_roberto: Conta = Conta(roberto)

print(conta_michael)
print(conta_roberto)
