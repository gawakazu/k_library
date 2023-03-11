from jobplace.models import ReservationModel#PublisherModel,AuthorModel,LibraryModel,BookModel,CustomUser,ReservationModel,HistoryModel,CommentModel
from jobplace.forms import LoginForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from pure_pagination.mixins import PaginationMixin
import datetime
def pagination(all,result,page,sort_order,user):
    #-------- ページネーション前処理
    everything = ReservationModel.objects.all()
    everything_l = [[i.book.id,i.book.book,i.book.author.author,i.book.publisher.publisher,i.book.year,i.limited_date,i.end_date,i.start_date,i.status,i.user.username] for i in everything]
    everything_lll = [i.book.book for i in everything]
    #print("----every---",everything_l)

    search = [i.book for i in result]
    search_list = []
    reserved_book = []

    #print('---serch----',search)
    #print('----se-------',sea)
    """
    for i in search:
        search_list.append(str(ReservationModel.objects.filter(book__book=i).count()))################0
        try:
            reserved_book.append(ReservationModel.objects.get(book__book=i,user=user))
        except:
            xxxx = 1#print('----no---')
    print('---search-L--',search_list)
    """
    sea = [0 for i in search]
    search_list = [str(everything_lll.count(search[i])) if search[i] in everything_lll else "0" for i in range(len(sea)) ]#0000000000000
    """"""
    #borrow_book = ReservationModel.objects.filter(user=user,start_date__gt="2000-01-01")
    #borrow_list = [i.book.id for i in borrow_book]#########2
    borrow_list = [i[0] for i in everything_l if i[-1]==str(user) and str(i[-3]) != "None"]#22222
    borr = borrow_list
    
    #print("---bl--",borrow_list)
    #print("---borr--",borr)

    result_list = [[i.id,i.images,i.book,i.author.author,i.publisher.publisher,i.year] for i in result]#########4
    """
    reserved_list = [i.book.id for i in reserved_book]
    reserved_list = [i for i in reserved_list if i not in borrow_list]#########1
    print('---resrved_list---',reserved_list)
    """
    borr_all = [i[0] for i in everything_l if i[-1]==str(user) and i[1] in search]
    reserved_list = list(set(borr_all) - set(borr))#111111
    #print('---resrved_list---',borr_all)
    """
    borrow_list2 = [[i.book.book,i.book.author.author,i.book.publisher.publisher,i.book.year,i.end_date,"-"] for i in borrow_book]
    t_book = ReservationModel.objects.filter(user=user,status="T")
    t_list = [[i.book.book,i.book.author.author,i.book.publisher.publisher,i.book.year,i.limited_date,1] for i in t_book]
    t_id_list = [i.book.id for i in t_book]
    borrow_t_list = borrow_list + t_id_list
    r_book = ReservationModel.objects.filter(user=user)
    reserved_list2 = [[i.book.book,i.book.author.author,i.book.publisher.publisher,i.book.year,i.end_date,0] for i in r_book if i.book.id not in borrow_t_list]
    book_list =  t_list + reserved_list2 + borrow_list2#########3
    print('--book_list--',book_list)
    """
    book_a = [[i[1],i[2],i[3],i[4],i[-4],'-'] for i in everything_l if (i[-1]==str(user) and i[1] in search and i[-2]==None) ]
    book_b = [[i[1],i[2],i[3],i[4],i[-5],0] for i in everything_l if (i[-1]==str(user) and i[1] in search and i[-2]=='1') ]
    book_c = [[i[1],i[2],i[3],i[4],i[-5],1] for i in everything_l if (i[-1]==str(user) and i[-2]=='T') ]
    book_list = book_c+book_b+book_a #333333
    #print('--book_list--',book_c+book_b+book_a)


    #-------- ページネーション前処理
    for i in range(len(result_list)):
        result_list[i].append(search_list[i])
    #print('-$$$$--',result_list)
    if sort_order ==5 or sort_order==2:
        sortsecond = lambda val: val[sort_order]
        result_list.sort(key=sortsecond,reverse=True)
    elif sort_order==3:
        sort_order -= 1
        sortsecond = lambda val: val[sort_order]
        result_list.sort(key=sortsecond)
        sort_order += 1
    else:
        sort_order += 1
        sortsecond = lambda val: val[sort_order]
        result_list.sort(key=sortsecond)
        sort_order -= 1
    #----  ページネーション
    page_document = all.split('|')[-1]
    page_number = page_document[page_document.find('page')+7:page_document.find('of')-1]
    job_paginator = Paginator(result_list,4)
    #page = self.request.GET.get('page')#, page_number)
    try:
        jobs = job_paginator.page(page)
    except PageNotAnInteger:
        if len(all.split('%')) > 1:
            jobs = job_paginator.page(all.split('%')[-1].split(' ')[1])
        elif "Page" in all.split('|')[-1]:
            jobs = job_paginator.page(all.split('|')[-1].split(' ')[1])
        else:
            jobs = job_paginator.page(1)
    except EmptyPage:
        jobs = job_paginator.page(1)
    #print('--borrow,reservation--',borrow_list,reserved_list)
    return jobs,reserved_list,sort_order,borrow_list,book_list#borrow_book_list2,current_borrow_list2