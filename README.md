# Auto Deposit ETH for HANA Network / Auto Grow and Open Garden 

## Description
**Support Multi Account**
- Register here : https://hanafuda.hana.network/dashboard
- Regist with Google
- Submit Code
  ```
  LCFUVA
  ```
- Deposit $1 to ETH BASE, just not too much.
- Make 5,000 transactions to earn 300/hour (to unlock cards and get points).
- Make 10,000 transactions to earn 643 Garden Rewards boxes (to unlock collection cards).

**If you have unlock collection cards end script**

## Instalation
```bash
git clone https://github.com/dekkeng/hanafuda.git
cd hanafuda
```
install the packages
```bash
pip install -r requirements.txt
```
**Edit prvkey.txt and input Private Key**
```bash
cp prvkey.txt.sample prvkey.txt
nano prvkey.txt
```
**Edit rtoken.txt and input Refresh token from instruction below**
```bash
cp rtoken.txt.sample rtoken.txt
nano rtoken.txt
```
run the script
```bash
python main.py
```

**choose 1 to do transactions**
or use shortcut command (change 1000 to amount of tx you need)
```bash
python main.py -a 1 -tx 1000
```

**choose 2 to run grow and open garden boxes**
or use shortcut command
```bash
python main.py -a 2
```

**How To Get Your Refresh Token**
- Open Hana Dashboard : https://hanafuda.hana.network/dashboard
- Click F12 to open console
- Find Application and choose session storage
- Select hana and copy your refreshToken
![image](image-2.png)
- Copy rtoken.txt.sample to rtoken.txt 
- Edit rtoken.txt paste your refresh token

## Optinally you can use pm2 to run script in the background
You can use pm2 to run your script in the background, allowing it to continue running even after you close your terminal.

### Installing pm2

If you haven't installed pm2, you can do so globally with npm:
```bash
npm install -g pm2
```
### Starting the Script with pm2
To run the script to execute 1000 transactions:
```bash
pm2 start main.py --name "hana-tx" --interpreter python -- -a 1 -tx 1000
```
To run the grow and garden actions:
```bash
pm2 start main.py --name "hana-grow" --interpreter python -- -a 2
```
## Managing pm2 Processes
You can manage your pm2 processes with the following commands:
- List running processes:
```bash
pm2 list
```
- Restart a process:
```bash
pm2 restart hana-tx
```
- Stop a process:
```bash
pm2 stop hana-tx
```
- View logs:
```bash
pm2 logs hana-tx
```