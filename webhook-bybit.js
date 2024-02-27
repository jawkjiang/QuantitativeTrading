const express = require('express');
const bodyParser = require('body-parser');
const dotenv = require('dotenv');
const {RestClientV5} = require('bybit-api');
const fs = require('fs');
const path = require('path');

// 加载环境变量
dotenv.config();

// 从环境变量中获取需要的数据
const {API_KEY1, API_SECRET1, API_KEY2, API_SECRET2} = process.env;

// 创建Bybit REST客户端
const client1 = new RestClientV5({
  key: API_KEY1,
  secret: API_SECRET1,
});
const client2 = new RestClientV5({
  key: API_KEY2,
  secret: API_SECRET2,
});

// 请求账户余额方法
async function getBalance(client, index) {
    try{
        const response = await client.getWalletBalance({
            accountType: 'UNIFIED',
            coin: 'USDT'
        });
        console.log(`账户${index}余额:`, response.result.list[0].coin[0].walletBalance);
        return response.result.list[0].coin[0].walletBalance;
    }
    catch(error){
        console.error('获取余额错误：', error);
        return undefined;
    }
}
// 提请交易方法
async function submitOrder(client, symbol, side, qty, reduceOnly, stopLoss=null) {
    try{
        const response = await client.submitOrder({
            category: 'linear',
            symbol: symbol,
            side: side,
            orderType: 'Market',
            qty: String(qty),
            reduceOnly: reduceOnly,
            stopLoss: stopLoss
        });
        console.log(response.retMsg);
        if (response.retCode === 0){
            console.log(`已提交订单，${side} ${qty} ${symbol}`);
        }
    }
    catch(error){
        console.error('提交订单错误：', error);
    }
}
// 获取当前价格方法
async function getPrice(client, symbol) {
    try{
        const response = await client.getTickers({
            category: 'linear',
            symbol: symbol});
        console.log(`${symbol} 当前价格: ${response.result.list[0].lastPrice}`);
        return response.result.list[0].lastPrice;
    }
    catch(error){
        console.error('获取价格错误：', error);
        return undefined;
    }
}

const filePath = path.join(__dirname, '/data.json');
const coin1 = ['TIAUSDT', 'ORDIUSDT', 'AUCTIONUSDT'];
const coin2 = ['BTCUSDT'];

(async () => {
    try {
        let balanceInit1 = await getBalance(client1, 1);
        let balanceInit2 = await getBalance(client2, 2);
        let lossBalance1 = balanceInit1 * 0.8;
        let lossBalance2 = balanceInit2 * 0.8;
        let coin1Index = 0;
        let coin2Index = 0;
        let data = {
            lossBalance1: lossBalance1,
            lossBalance2: lossBalance2,
            coin1Index: coin1Index,
            coin2Index: coin2Index
        }
        fs.writeFileSync(filePath, JSON.stringify(data), 'utf8');
        console.log('数据初始化完成');
    } catch (error) {
        console.error('API验证错误：', error);
    }
})();

const app = express();
const PORT = process.env.PORT || 80;

// 设置中间件来解析JSON格式的请求体
app.use(bodyParser.json());

// POST路由来接收webhook
app.post('/webhook', async (req, res) => {
  // 解析收到的JSON数据
  console.log(req.body);
  const {symbol, action} = req.body;

  // 读取JSON文件中的数据
  const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  let {lossBalance1, lossBalance2, coin1Index, coin2Index} = data;

  if(coin1[coin1Index] === symbol) {
    if(coin1Index === coin1.length){
        console.log('账户1所有币种已平仓，不再进行交易');
        res.status(200).send('Webhook received');
        return;
    }
    if(action === 'buy') {
        await submitOrder(client1, symbol, 'Buy', 0, true);
        }
    else if(action === 'sell') {
        await submitOrder(client1, symbol, 'Sell', 0, true);
        }
    let balance1 = await getBalance(client1, 1);
    console.log('已平仓'+coin1[coin1Index]+'，当前账户余额为'+balance1)

    if (balance1 * 0.8 > lossBalance1) {
        lossBalance1 = balance1 * 0.8;
        console.log('由于划转资金变更，止损线已调整为'+lossBalance1);
    }

    if(balance1 < lossBalance1) {
        console.log('账户1余额低于止损线，已强平，当前账户余额为'+balance1);
        coin1Index++;
        lossBalance1 = balance1 * 0.8;
        const saveData = {
          lossBalance1: lossBalance1,
          lossBalance2: lossBalance2,
          coin1Index: coin1Index,
          coin2Index: coin2Index
        }
        fs.writeFileSync(filePath, JSON.stringify(saveData), 'utf8');
        console.log('数据已保存');
        res.status(200).send('Webhook received');
        return;
    }

    let currentPrice = await getPrice(client1, symbol);
    // 计算买量
    let qty = Math.floor(balance1 / currentPrice * 10) / 10;
    if(action === 'buy') {
        let lossPrice = Math.floor(lossBalance1 / balance1 * currentPrice * 1000) / 1000;
        await submitOrder(client1, symbol, 'Buy', qty, false, String(lossPrice));
        }
    else if(action === 'sell') {
        let lossPrice = Math.floor(balance1 / lossBalance1 * currentPrice * 1000) / 1000;
        await submitOrder(client1, symbol, 'Sell', qty, false, String(lossPrice));
        }
  }


  else if(coin2[coin2Index] === symbol) {
    if(coin2Index === coin2.length){
        console.log('账户2所有币种已平仓，不再进行交易');
        res.status(200).send('Webhook received');
        return;
    }
    if(action === 'buy') {
        await submitOrder(client2, symbol, 'Buy', 0, true);
        }
    else if(action === 'sell') {
        await submitOrder(client2, symbol, 'Sell', 0, true);
        }
    let balance2 = await getBalance(client2, 2);
    console.log('已平仓'+coin2[coin2Index]+'，当前账户余额为'+balance2)

    if (balance2 * 0.8 > lossBalance2) {
        lossBalance2 = balance2 * 0.8;
        console.log('由于划转资金变更，止损线已调整为'+lossBalance2);
    }

    if(balance2 < lossBalance2) {
        console.log('账户2余额低于止损线，已强平，当前账户余额为'+balance2);
        coin2Index++;
        lossBalance2 = balance2 * 0.8;
        const saveData = {
            lossBalance1: lossBalance1,
            lossBalance2: lossBalance2,
            coin1Index: coin1Index,
            coin2Index: coin2Index
        }
        fs.writeFileSync(filePath, JSON.stringify(saveData), 'utf8');
        console.log('数据已保存');
        res.status(200).send('Webhook received');
        return;
    }

    let currentPrice = await getPrice(client2, symbol);
    // 计算买量
    let qty = Math.floor(balance2 / currentPrice * 10) / 10;
    if(action === 'buy') {
        let lossPrice = Math.floor(lossBalance2 / balance2 * currentPrice * 1000) / 1000;
        await submitOrder(client2, symbol, 'Buy', qty, true, String(lossPrice));
        }
    else if(action === 'sell') {
        let lossPrice = Math.floor(balance2 / lossBalance2 * currentPrice * 1000) / 1000;
        await submitOrder(client2, symbol, 'Sell', qty, true, String(lossPrice));
        }
  }

  // 将数据存储到JSON文件中
  const saveData = {
    lossBalance1: lossBalance1,
    lossBalance2: lossBalance2,
    coin1Index: coin1Index,
    coin2Index: coin2Index
  }
    fs.writeFileSync(filePath, JSON.stringify(saveData), 'utf8');
    console.log('数据已保存');
    res.status(200).send('Webhook received');

})

// 启动服务器
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});