from jobplace.models import ReservationModel#PublisherModel,AuthorModel,LibraryModel,BookModel,CustomUser,ReservationModel,HistoryModel,CommentModel
from jobplace.forms import LoginForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from pure_pagination.mixins import PaginationMixin
def pagination(all,result,page,sort_order,user):
    #-------- ページネーション前処理
    search = [i.book for i in result]
    search_list = []
    reserved_book = []
    for i in search:
        search_list.append(str(ReservationModel.objects.filter(book__book=i).count()))
        try:
            reserved_book.append(ReservationModel.objects.get(book__book=i,user=user))
        except:
            xxxx = 1#print('----no---')

    borrow_book = ReservationModel.objects.filter(user=user,start_date__gt="2000-01-01")
    borrow_list = [i.book.id for i in borrow_book]
    result_list = [[i.id,i.images,i.book,i.author.author,i.publisher.publisher,i.year] for i in result]
    reserved_list = [i.book.id for i in reserved_book]
    reserved_list = [i for i in reserved_list if i not in borrow_list]
    borrow_list2 = [[i.book.book,i.book.author.author,i.book.publisher.publisher,i.book.year,i.end_date,"-"] for i in borrow_book]
    r_book = ReservationModel.objects.filter(user=user)
    reserved_list2 = [[i.book.book,i.book.author.author,i.book.publisher.publisher,i.book.year,i.end_date,0] for i in r_book if i.book.id not in borrow_list]
    book_list =  reserved_list2 + borrow_list2

    #-------- ページネーション前処理
    for i in range(len(result_list)):
        result_list[i].append(search_list[i])
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