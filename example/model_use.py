# -*- coding:utf-8 -*-
"""
本文件介绍 model 相关的操作，作为学习范例
这里以 UserModel 举例
"""

import sys
import logging
sys.path.insert(1, '..')

from mongoengine.queryset.visitor import Q
from adam.flask_app import Adam
from models.user import User
from models.enums import UserEnum
app = Adam(enable_celery=True)


################ 查询 ###########################

# 查询一条数据
user_obj = User.objects.get(id='6679435754deefcb7b0fe650')
logging.info(f'取到用户： {user_obj.user_name}')

user_obj2 = User.objects.filter(id='6679435754deefcb7b0fe650').first()
# user_obj2 = User.objects(pk='6679435754deefcb7b0fe650').first()  # 效果同上。 直接将条件写到 objects 也是可以的， id 字段也可以写成 pk
logging.info(f'再次取到用户： {user_obj2.user_name}')

'''
注意：
虽然 get() 和 first() 两个函数都可以用来获取一条数据，但两者有以下区别
- get() 查不到条件时会报错 <models.system.user.DoesNotExist>
- first() 查不到条件时会返回 None
- get() 查到多条记录时会报错 <models.system.user.MultipleObjectsReturned>
- first() 查到多条记录时会返回查到的第一条
'''


# 查询多条数据
users = User.objects.filter(user_type=UserEnum.USER).all()
# users = User.objects.filter(user_type=UserEnum.USER)  # 这样写也行，跟上面同样效果
logging.info(f'取到{users.count()}个用户')


# 排序
# order_by 函数指定，+或者没符号表示升序，-表示降序
first_user = User.objects.order_by("+created_at").first()
logging.info(f'order_by 取到用户： {first_user.user_name}')
# 多个排序条件
second_user = User.objects.order_by("+user_type", "-created_at").first()
logging.info(f'order_by 多个字段取到用户： {second_user.user_name}')

# 查询结果个数限制
# 跟传统的ORM一样，MongoEngine也可以限制查询结果的个数。一种方法是在QuerySet对象上调用limit和skip方法；另一种方法是使用数组的分片的语法。例如：
users1 = User.objects[2:15]  # 下标从 0 开始
logging.info(f'取到{len(list(users1))}个用户')  # 注意：结果集是延迟加载的，所以必须用 list() 括起来，强制查询出结果

users2 = User.objects.skip(1).limit(15)  # skip 下标从 0 开始
logging.info(f'取到{len(list(users2))}个用户')

# 统计
# count() 默认忽略 limit 和 skip 来统计。 设参数 count(True) 统计 limit 和 skip 后的
logging.info(f'count无参数统计到 {users2.count()} 个用户')
logging.info(f'count参数 True 统计到 {users2.count(True)} 个用户')


# 复杂条件查询
# <字段名> + '__函数名' 可以执行复杂查询
c_users = User.objects.filter(user_name__contains='c')
logging.info(f'取到 user_name 中包含字母 c 的 {len(list(c_users))} 个用户')
nc_users = User.objects.filter(user_name__not__contains="c")
logging.info(f'取到 user_name 中不包含字母 c 的 {len(list(nc_users))} 个用户')

# in 查询
in_users = User.objects.filter(pk__in=['66ac5a4646e8c895e1006eda', '66b07dd655fb4b2399fd3fd5'])
logging.info(f'in查询取 {len(list(in_users))} 个用户')

# 内嵌查询
# 查询 others 字段中的 projects 值不为空列表
users = app.models['User'].objects.filter(others__projects__ne=[]).all()
logging.info(f'内嵌查询到 {users.count()} 个用户')

# or 查询 | 复杂条件查询
queryset = User.objects()
if 1 == 1:  # 复杂条件查询，使用多次 filter 处理。 这里的 if 模拟需要判断的多个条件
    queryset = queryset.filter(is_delete__ne=True)
if 2 == 2:  # or 查询使用多个 Q 来处理
    queryset = queryset.filter(Q(user_name='user_name') | Q(mobile='135..4565') | Q(email='dd@144.cn'))
# 这用户的查询条件是: is_delete != true AND (user_name='user_name' OR mobile='135..4565' OR email='dd@144.cn')
or_user = queryset.first()


'''
# 列举出各函数
__exact  # 精确等于 like 'aaa'
__iexact  # 精确等于 忽略大小写 ilike 'aaa'
__contains  # 包含 like '%aaa%'
__icontains  # 包含 忽略大小写 ilike '%aaa%'，但是对于sqlite来说，contains的作用效果等同于icontains。
__gt  # 大于
__gte  # 大于等于
__lt  # 小于
__lte  # 小于等于
__in  # 存在于一个list范围内
__nin  # 值不在列表中(索引不会生效，全表扫描)
__startswith  # 以…开头
__istartswith  # 以…开头 忽略大小写
__endswith  # 以…结尾
__iendswith  # 以…结尾，忽略大小写
__ne  # 不相等
__not  # 取反
__all  # 与列表的值相同
__mod  # 取模
__size  # 数组的大小
__exists  # 字段的值存在
__match  # 使你可以使用一整个document与数组进行匹配查询list
#对于大多数字段，这种语法会查询出那些字段与给出的值相匹配的document，但是当一个字段引用 ListField 的时候，而只会提供一条数据，那么包含这条数据的就会被匹配上：

# 上面没有判断是否为空的函数，所以改成下面的判断
__ne=None  # 不为空
<字段名>=None  # 为空
'''


################ 新增 ###########################

logging.info(f'新增前有 {User.objects.count()} 个用户')
kingname = User(user_name='kingname', email='kingname@qq.com', user_type=UserEnum.MANAGER)
kingname.save()

# 当然，我们也可以这样写：
new_name = User(user_name='new_name', user_type=UserEnum.MANAGER, password='abcd1234')
new_name.email = 'new_name@qq.com'
new_name.save()

# 也可以用 create 函数创建
b = User.objects.create(user_name='User A', user_type=UserEnum.MANAGER)

# 批量新增
User.objects.insert([
    User(user_name='User B', user_type=UserEnum.MANAGER),
    User(user_name='User C', user_type=UserEnum.MANAGER)
])
logging.info(f'新增后有 {User.objects.count()} 个用户')


################ 更新 ###########################

# 修改一条数据
up_user = User.objects(user_type=UserEnum.MANAGER).first()
up_user.password = '123456'
up_user.others = {'aa': 12345}
up_user.save()  # 如果数据出错，会产生一个 ValidationError 错误
# up_user.save(validate=False)  # 不会抛出 ValidationError

# 修改一条数据, 只修改匹配到的第一条
User.objects.filter(user_name='User A', user_type=UserEnum.MANAGER).update_one(is_delete=False)
logging.info(f"检查更新结果, is_delete={User.objects(user_name='User A').first().is_delete}")

# 批量更新
User.objects.filter(user_type=UserEnum.MANAGER).update(nickname='update name')
manage_count = User.objects.filter(user_type=UserEnum.MANAGER).count()
update_count = User.objects.filter(nickname='update name').count()
logging.info(f"检查更新结果, manage_count:{manage_count}, update_count:{update_count}")

'''
对一个QuerySet()使用 update_one() 或 update() 来实现更新，有一些可以与这两个方法结合使用的操作符

    set – 设置成一个指定的值强调内容
    unset – 删除一个指定的值
    inc – 将值加上一个给定的数
    dec – 将值减去一个给定的数
    pop – 将 list 里面的 最前/最后 一项移除。 传参 1 是移除最后一项，传参 -1 是移除最前一项，只能传这两个参数
    push – 在 list 最后添加一个值
    push_all – 在 list 里面添加好几个值， 要求传参是 list 。
    pull – 将一个值从 list 里面移除, 参数不存在不会报错。
    pull_all – 将好几个值从 list 里面移除， 要求传参是 list, 参数不存在不会报错。
    add_to_set – 如果list里面没有这个值，则添加这个值自动更新的语法与查询的语法基本相同，区别在于操作符写在字段之前：*
'''
User.objects(id=up_user.id).update_one(set__others={'bb': 654})
up_user2 = User.objects(id=up_user.id).first()
logging.info(f"检查更新结果, up_user2.others:{up_user2.others}")

################ 删除 ###########################

logging.info(f'删除前有 {User.objects.count()} 个用户')

# 删除一条数据
delete_user = User.objects.filter(user_type=UserEnum.MANAGER).first()
delete_user.delete()
logging.info(f'删除一个用户后，剩 {User.objects.count()} 个用户')

# 批量删除
User.objects.filter(user_type=UserEnum.MANAGER).delete()
logging.info(f'删除后有 {User.objects.count()} 个用户')


################ 关联外键 ###########################

# 查询出 use.default_project 的结果
user = User.objects(default_project__ne=None).first()
logging.info(f'关联用户的project {type(user.default_project)}: {user.default_project.id}')

# 必须使用 fetch() 才会关联查询出结果，否则只能点出 id，点其它字段会报错
project = user.default_project.fetch()
logging.info(f'关联查询出 用户的project {type(project)}: {project.to_dict()}')


# 外键更新
user2 = User.objects(default_project=None).first()
# user2.default_project = '66b091da55fb4b2399fd3ff5'  # 关联字段可以 直接赋值一个id
user2.default_project = project  # 也可以赋值一个 Model 实例
# user2.save()

# 反射出 model 的所有字段
_fields = User._fields
logging.info(f'反射出 User model 的所有字段 {type(_fields)}: {_fields}')

################ 其它 ###########################

# mongodb 对象转成 dict
user = User.objects.first()
data = user.to_dict(exclude_fields=['_cls', 'others'])  # exclude_fields 排除的字段名
logging.info(f'to_dict 用户的结果 {data}')


# 使用原生语句
collection = User._get_collection()  # 获取 Model 对应的 collection
user_list = list(collection.find().sort([("_id", 1)]).limit(2))
logging.info(f'原生查询的结果 {user_list}')

db_client = User._get_db()
project_collection = db_client['project']
project_list = list(project_collection.find().sort([("_id", 1)]).limit(2))
logging.info(f'原生 project 查询的结果 {project_list}')

