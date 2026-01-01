import sounddevice as sd
import numpy as np
import librosa
import scipy.io.wavfile as wav

def capturar_assinatura():
    fs = 22050  # Frequência de amostragem
    segundos = 5
    print(f"Gravando {segundos} segundos... Fale naturalmente.")
    
    # Grava o áudio do microfone
    gravacao = sd.rec(int(segundos * fs), samplerate=fs, channels=1)
    sd.wait()  # Espera terminar a gravação
    print("Gravação finalizada!")

    # Extrai os MFCCs (características únicas da voz)
    y = gravacao.flatten()
    mfccs = librosa.feature.mfcc(y=y, sr=fs, n_mfcc=13)
    assinatura = np.mean(mfccs.T, axis=0)

    # Salva a assinatura em um arquivo
    np.save("minha_assinatura.npy", assinatura)
    print("Calibração salva com sucesso no arquivo: minha_assinatura.npy")

if __name__ == "__main__":
    capturar_assinatura()