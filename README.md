# obsidian_backend
[toc]
## API
### Lighten's
####  获取文档编辑历史

- 通信方式：POST (Json)
- url:doc/get_history/

- 发送包：
    - doc_id: 正整形， 表示文档id
- 返回包：
    - success: 布尔值 true/false
    - exc: 字符串，错误信息
    - history: 数组，元素为记录，格式如下：
        - time: 字符串，编辑时间
        - username: 字符串，用户名
        - avatar: 字符串，头像链接

####  获取该文档内所有评论

通信方式：POST (Json)   
urls: comment/get/

发送包：
- doc_id: 正整形， 表示文档id
返回包：
- success: 布尔值 true/false
- exc: 字符串，错误信息
- comments: 数组，里为每个对象里包含两个评论对象。
[ {comment: 评论对象，reply: 评论回复的对象（回复哪条就是哪条）} ]
评论对象格式：
{
- com_id: 评论id
- content：评论内容
- create_time: 评论事件
- username：用户名
- avatar：头像链接
- reply_comments: {
    - com_id:
    - content:
    - create_time
    - username
    - avatar

若无回复，reply则为0

注意：若无权限应该获取失败。

comment/get/

