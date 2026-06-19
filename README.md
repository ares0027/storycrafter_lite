# Storycrafter Lite v0.2

Storycrafter Lite is a powerful, standalone tool designed to extract metadata from books and perfectly correct Full Book OCR (Optical Character Recognition) scans using Local or Cloud LLMs. 

This repository strips down the main Storycrafter engine to provide just the two core features in a clean, dual-language (English/Turkish) interface.

## Features

### 1. Book Information Extractor
- Upload your `PDF`, `EPUB`, `DOCX`, or `TXT` file.
- The system extracts the first chunk of text from the book.
- Click **"Ask LLM for Information"** to automatically extract and populate the book's Title, Author, Genre, Original Language, Publication Date, and Style.
- Save this metadata to your local library.

### 2. Full Book OCR Corrector
- Tired of garbled text, split words, and scanning artifacts from old books? 
- This tool runs an asynchronous, chunk-based rolling correction over the **entire length of your book**.
- It uses smart overlapping to maintain narrative context between chunks.
- Sit back and watch the LLM perfectly repair the text, chunk by chunk, without altering the author's words.

## Prerequisites
- **Python 3.10+**: This is the only software you need installed on your machine. The `start.bat` script handles everything else.

## How to Install & Run (Windows)

It is highly recommended to run this locally. 

1. **Download the Repository** to your local machine.
2. Double-click **`start.bat`**.
3. The script will automatically create a Python virtual environment, install the necessary dependencies, and start the local FastAPI server.
4. Open your browser and navigate to `http://localhost:8000`.

---

# Storycrafter Lite v0.2 (Türkçe)

Storycrafter Lite, kitaplardan meta veri çıkarmak ve Yerel veya Bulut LLM'leri kullanarak Tam Kitap OCR (Optik Karakter Tanıma) taramalarını kusursuz bir şekilde düzeltmek için tasarlanmış güçlü, bağımsız bir araçtır.

Bu depo, ana Storycrafter motorunu küçülterek sadece iki temel özelliği temiz, çift dilli (İngilizce/Türkçe) bir arayüzde sunar.

## Özellikler

### 1. Kitap Bilgi Çıkarıcı
- `PDF`, `EPUB`, `DOCX` veya `TXT` dosyanızı yükleyin.
- Sistem, kitabın ilk metin bölümünü çıkarır.
- Kitabın Başlığını, Yazarını, Türünü, Orijinal Dilini, Yayın Tarihini ve Stilini otomatik olarak çıkarmak ve doldurmak için **"LLM'ye Bilgi Sor"** düğmesine tıklayın.
- Bu meta verileri yerel kütüphanenize kaydedin.

### 2. Tam Kitap OCR Düzeltici
- Eski kitaplardaki bozuk metinlerden, bölünmüş kelimelerden ve tarama hatalarından bıktınız mı?
- Bu araç, **kitabınızın tamamı** üzerinde asenkron, parça tabanlı bir düzeltme işlemi yürütür.
- Parçalar arasında anlatım bağlamını korumak için akıllı örtüşme kullanır.
- Arkanıza yaslanın ve LLM'nin yazarın kelimelerini değiştirmeden metni parça parça mükemmel bir şekilde onarmasını izleyin.

## Gereksinimler
- **Python 3.10+**: Bilgisayarınızda kurulu olması gereken tek yazılım budur. Geri kalan her şeyi `start.bat` dosyası halleder.

## Nasıl Kurulur ve Çalıştırılır (Windows)

Bunu yerel olarak çalıştırmanız şiddetle tavsiye edilir.

1. **Depoyu İndirin** bilgisayarınıza.
2. **`start.bat`** dosyasına çift tıklayın.
3. Komut dosyası otomatik olarak bir Python sanal ortamı oluşturacak, gerekli bağımlılıkları yükleyecek ve yerel FastAPI sunucusunu başlatacaktır.
4. Tarayıcınızı açın ve `http://localhost:8000` adresine gidin.
