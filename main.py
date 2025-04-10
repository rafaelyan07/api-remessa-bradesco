
from flask import Flask, request, jsonify, send_file
from datetime import datetime
import os

app = Flask(__name__)

def format_boleto_linha_1(boleto, index, cod_benef):
    cpf_cnpj = boleto.get('cpf_cnpj', '').zfill(14)
    valor = str(int(float(boleto.get('valor', 0)) * 100)).zfill(15)
    nosso_numero = str(boleto.get('nosso_numero', '')).zfill(10)
    vencimento = datetime.strptime(boleto['vencimento'], '%Y-%m-%d').strftime('%d%m%y')
    emissao = datetime.strptime(boleto['data_emissao'], '%Y-%m-%d').strftime('%d%m%y')
    nome = boleto.get('nome', '')[:40].ljust(40)
    endereco = boleto.get('endereco', '')[:40].ljust(40)
    cep = boleto.get('cep', '')[:8].zfill(8)
    sequencial = str(index + 2).zfill(6)

    linha = (
        "1" +
        cpf_cnpj +
        "0000000000" +
        cod_benef +
        " " * 25 +
        valor +
        nosso_numero +
        "1N           0  01" +
        vencimento +
        emissao +
        "0000000000000000" * 3 +
        "1N" +
        str(index + 1).zfill(6) +
        cpf_cnpj +
        nome +
        endereco +
        cep +
        " " * 60 +
        sequencial
    )
    return linha[:400]

def format_boleto_linha_2(boleto, index, cod_benef):
    valor = str(int(float(boleto.get('valor', 0)) * 100)).zfill(15)
    nosso_numero = str(boleto.get('nosso_numero', '')).zfill(10)
    sequencial = str(index + 3).zfill(6)
    linha = (
        "2APOS O VENCIMENTO COBRAR MULTA DE 2% E JUROS DE 1% AO MES." +
        " " * 22 +
        "DUVIDAS CONTATO COM  RENATA - E-MAIL: RENATA@AOJESP.ORG.BR" +
        " " * 22 +
        "REFERENTE AO MES DE MAIO/2025" +
        " " * 51 +
        "CONVENIO MEDICO=R$ " +
        boleto.get("valor_formatado", "0,00").rjust(10) +
        " " * 98 +
        cod_benef +
        nosso_numero +
        valor +
        sequencial
    )
    return linha[:400]

def gerar_remessa(dados):
    cod_benef = dados.get('beneficiario', {}).get('codigo', '0090162800245348')

    header = (
        "01REMESSA01COBRANCA       00000000000005326606ASS.DOS OFICIAIS DE JUSTICA DO"
        "237BRADESCO       " + datetime.now().strftime("%d%m%y") +
        "        MX9000283" + " " * 294 + "000001"
    )

    linhas = [header]

    for i, boleto in enumerate(dados.get("boletos", [])):
        linha1 = format_boleto_linha_1(boleto, i, cod_benef)
        linha2 = format_boleto_linha_2(boleto, i, cod_benef)
        linhas.append(linha1)
        linhas.append(linha2)

    trailer = "9" + " " * 393 + str(len(linhas) + 1).zfill(6)
    linhas.append(trailer)

    return "\r\n".join(linhas)

@app.route("/gerar-remessa", methods=["POST"])
def gerar():
    dados = request.json
    conteudo = gerar_remessa(dados)
    nome_arquivo = f"remessa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.rem"
    caminho = os.path.join("remessas", nome_arquivo)

    os.makedirs("remessas", exist_ok=True)
    with open(caminho, "w") as f:
        f.write(conteudo)

    return jsonify({"download_url": f"/download/{nome_arquivo}"})


@app.route("/download/<nome_arquivo>", methods=["GET"])
def download(nome_arquivo):
    caminho = os.path.join("remessas", nome_arquivo)
    if os.path.exists(caminho):
        return send_file(caminho, mimetype="text/plain", as_attachment=True)
    else:
        return "Arquivo não encontrado", 404
