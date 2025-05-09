# import wikipediaapi
# from opencc import OpenCC

# class WikiSearcher(object):
#     def __init__(self) -> None:
#         # 设置简体转繁体转换器
#         self.cc = OpenCC('s2t')

#         # 指定合法的 user-agent 避免 Wikipedia 拒绝请求
#         self.wiki = wikipediaapi.Wikipedia(
#             language='zh',
#             user_agent='KGLLM/1.0 (contact@example.com)'  # 改成你的实际邮箱或描述
#         )

#     def search(self, query: str):
#         """
#         根据查询词查找 Wikipedia 中文页面，尝试简繁转换回退。
#         """
#         try:
#             # 尝试原始查询
#             page = self.wiki.page(query)
#             if page.exists():
#                 return page

#             # 简体转繁体重试
#             converted_query = self.cc.convert(query)
#             if converted_query != query:
#                 page = self.wiki.page(converted_query)
#                 if page.exists():
#                     return page

#         except Exception as e:
#             print(f"❌ Wiki 搜索失败: {e}")

#         return None
# # if __name__ == "__main__":
# #     searcher = WikiSearcher()

# #     queries = ["人工智能", "不存在的词条"]

# #     for q in queries:
# #         page = searcher.search(q)
# #         if page:
# #             print(f"✅ 查询成功：{page.title}")
# #             print(page.summary[:100])
# #         else:
# #             print(f"❌ 查询失败：{q}")
