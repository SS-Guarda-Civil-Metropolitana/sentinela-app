import sounddevice as sd
import numpy as np
import librosa
import speech_recognition as sr
from scipy.spatial.distance import cosine
import noisereduce as nr
import requests
import geocoder


def enviar_alerta_ssp(frase, precisao):
    g = geocoder.ip('me')
    payload = {
        "usuario": "Henrique - ID 001",
        "mensagem": frase,
        "confianca": f"{precisao*100:.2f}%",
        "localizacao": g.latlng
    }
    
    try:
        # Tenta enviar para o seu servidor local
        resposta = requests.post("http://127.0.0.1:5000/alerta", json=payload)
        if resposta.status_code == 200:
            print(">>> Alerta entregue com sucesso à Central!")
    except:
        print(">>> Falha ao conectar com a Central de Segurança.")
# 1. Carregar sua assinatura calibrada
assinatura_mestra = np.load("minha_assinatura.npy")

def analisar_voz(audio_data, sr_rate):
    # Extrai os MFCCs do áudio que acabou de ser ouvido
    mfccs = librosa.feature.mfcc(y=audio_data, sr=sr_rate, n_mfcc=13)
    assinatura_atual = np.mean(mfccs.T, axis=0)
    
    # Calcula a similaridade (Distância Cosseno)
    similaridade = 1 - cosine(assinatura_mestra, assinatura_atual)
    return similaridade

def iniciar_vigilancia():
    reconhecedor = sr.Recognizer()
    fs = 22050
    
    with sr.Microphone() as source:
        print(">>> SISTEMA DE SEGURANÇA ATIVO <<<")
        reconhecedor.adjust_for_ambient_noise(source)
        
        while True:
            try:
                # Ouve por um curto período
                audio = reconhecedor.listen(source, phrase_time_limit=4)
                
                # Converte para texto para ver se há palavra de risco
                texto = reconhecedor.recognize_google(audio, language="pt-BR").lower()
                
                palavras_de_risco = ["socorro", "ajuda", "polícia", "meu deus"]
                
                if any(p in texto for p in palavras_de_risco):
                    # Se detectou a palavra, agora verifica se é a SUA VOZ
                    data = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(float)
                    # Redução de ruído para precisão de 99%
                    data_clean = nr.reduce_noise(y=data, sr=fs)
                    
                    confianca = analisar_voz(data_clean, fs)
                    
                    if confianca > 0.85: # Ajuste para 0.99 conforme os testes
                        print(f"!!! ALERTA CONFIRMADO ({confianca*100:.2f}%) !!!")
                        print(f"Evento: {texto}")
                        enviar_alerta_ssp(texto, confianca)
                    else:
                        print(f"Palavra de risco ignorada. Voz não reconhecida. (Confiança: {confianca*100:.2f}%)")
            
            except Exception:
                pass

def enviar_alerta_ssp(frase, precisao):
    # Aqui simulamos o envio para a Secretaria de Segurança
    print(f"ENVIANDO PARA SSP... Localização: [GPS SIMULADO] | Áudio: '{frase}'")

if __name__ == "__main__":
    iniciar_vigilancia()

    