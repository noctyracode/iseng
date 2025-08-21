#!/bin/bash
echo "Membuat/Mengupdate .env file..."

read -p "Masukkan Owner ID: " OWNER_ID
read -p "Masukkan API ID: " API_ID
read -p "Masukkan API HASH: " API_HASH
read -p "Masukkan BOT TOKEN: " BOT_TOKEN
read -p "Masukkan MongoDB URL: " MONGO_DB
read -p "Masukkan DB Name: " DB_NAME

cat > .env <<EOL
OWNER_ID=$OWNER_ID
API_ID=$API_ID
API_HASH=$API_HASH
BOT_TOKEN=$BOT_TOKEN
MONGO_DB=$MONGO_DB
DB_NAME=$DB_NAME
EOL

echo ".env berhasil dibuat!"
