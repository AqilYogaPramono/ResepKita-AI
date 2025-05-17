from rapidfuzz import process

kamus_bahan = ["telur", "tomat", "bawang", "ayam", "susu"]

def cari_bahan(teks):
    kata_user = teks.lower().split()
    bahan_dikenali = []
    for kata in kata_user:
        match, skor, _ = process.extractOne(kata, kamus_bahan)
        if skor > 60:
            bahan_dikenali.append(match)
    return list(set(bahan_dikenali))

if __name__ == "__main__":
    input_user = input("Masukkan bahan makanan: ")
    hasil = cari_bahan(input_user)
    
    if hasil:
        print("Bahan dikenali:", hasil)
    else:
        print("Mohon maaf, Tidak ada bahan yang cocok")
        print("Mari berkontibusi dengan membagikan resep sesuai keiginan anda\n")
