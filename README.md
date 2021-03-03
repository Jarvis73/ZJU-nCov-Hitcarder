# ZJU-nCov-Hitcarder

浙大nCov肺炎健康打卡定时自动脚本

 - 可给定锚点时间，默认为每天8点15分，实际打卡时间在锚点时间上下各浮动2小时
 - 默认每次提交上次所提交的内容（只有时间部分更新）
 - 系统表单如有更新，在当天自行手机打卡，后面会自动按照你更新后的选项继续打卡

 项目用于学习交流，仅用于各项无异常时打卡，如有身体不适等情况还请自行如实打卡~

<img src="https://github.com/Tishacy/ZJU-nCov-Hitcarder/raw/master/demo.png" width="500px"/>

> 感谢[conv1d](https://github.com/conv1d)同学，已使用requests直接登录浙大统一认证平台，不再依赖phantomjs

## Usage

1. clone本项目（为了加快clone速度，可以指定clone深度`--depth 1`，只克隆最近一次commit），并cd到本目录
    ```bash
    $ git clone https://github.com/Tishacy/ZJU-nCov-Hitcarder.git --depth 1
    $ cd ZJU-nCov-Hitcarder
    ```
    
2. 安装依赖

    ```bash
    $ pip3 install -r requirements.txt
    ```

3. 启动定时自动打卡脚本

* 不使用配置文件，手动输入用户名密码

```bash
$ python3 checkin.py
```

* 使用配置文件，用户名密码填入配置文件 `config.json`
  
```javascript
{
    "username": "你的浙大统一认证平台用户名",
    "password": "你的浙大统一认证平台密码",
    "schedule": {
        "hour": "8",     // 8点
        "minute": "15"   // 15分 
    }
}
```

启动自动打卡脚本

```bash
$ python3 checkin.py -c
```

## Tips

- 为了防止电脑休眠或关机时程序不运行，推荐把这个部署到VPS上
- 测试程序是否正常运行：可以先把定的时间放在最近的一个时间（比如下一分钟）看下到时间是否可以正常打卡
- 想指定自己打卡地理位置的童鞋可以参考[8#issue](https://github.com/Tishacy/ZJU-nCov-Hitcarder/issues/8#issue-565719250)


## Thanks

感谢贡献者

<a href="https://github.com/conv1d"><img src="https://avatars2.githubusercontent.com/u/24759956" width="100px" height="100px"></a>


## LICENSE

Copyright (c) 2020 tishacy.

Licensed under the [MIT License](https://github.com/Tishacy/ZJU-nCov-Hitcarder/blob/master/LICENSE)



