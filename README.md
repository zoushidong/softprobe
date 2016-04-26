

在探针上应对ssh_config进行配置：
	StrictHostKeyChecking no

服务器应至少有两个账号：
	一个账号拥有写权限，可以push (供管理员修改使用) 账号名为sprobe
	一个账号没有写权限，只能pull (供探针使用) 账号名为git

＃＃＃＃＃＃以上信息作废＃＃＃＃＃＃

服务器自身应通过sprobe账号glone一个copy，供生成commits.json

服务器应可以利用证书登录sprobe账户

该项目应和服务器项目放在同一目录下，以便于commits.json文件的生成

服务器端repository应有如下hook (post-receive):
	#!/bin/sh
	cd /home/sprobe/probe #此处应为服务器端clone的路径
	env -i git pull origin master
	env -i python parse_git_log.py
	#以上hook将在~目录生成commits.json文件，列出该系统所有版本信息

commits.json 文件格式 : 
	{
        "commit_id": "3563ac334b314cf745c0250da03da3191e9d9102",
        "date": "Sun Aug 30 11",
        "content": "",
        "email": "342159837@qq.com",
        "author": "hyd"
    },

