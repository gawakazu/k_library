from django.views.generic import ListView,TemplateView,RedirectView,CreateView,DeleteView,UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin,PermissionRequiredMixin,UserPassesTestMixin
from django.contrib.auth import login,logout,authenticate,views as auth_views
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from pure_pagination.mixins import PaginationMixin
from .models import PublisherModel,AuthorModel,LibraryModel,BookModel,CustomUser,ReservationModel,HistoryModel,CommentModel
from .forms import LoginForm
import paginator
import mojimoji
import datetime
import jaconv
import MeCab

### 図書のメイン画面で、書籍の検索を可能とする。地図、情報、暦を表示する。
class MainView(TemplateView):
    template_name = 'main.html'
    model = CommentModel
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        # commentModelに記載の情報をメイン画面に表示。
        comment_queryset = CommentModel.objects.all()
        comment_data = [[i.comment.replace('\\n','\n'),i.status] for i in comment_queryset]
        context['comment_data'] = comment_data
        return context
    def post(self,request,*args,**kwargs):
        context = super().get_context_data(**kwargs)
        # かんたん検索の入力文字に、'|<Page 1 of 1>2?'を加え検索結果(result）へ。ﾍﾟｰｼﾞﾈｰｼｮﾝの画面遷移と合わせるため。
        kensaku = request.POST['kantan']
        kensaku = kensaku + '|<Page 1 of 1>2?'
        # 未入力の場合、メインに戻す。
        if kensaku == '|<Page 1 of 1>2?' :
            return redirect('main')
        return redirect('result',kensaku)

### 検索結果を表示する。予約の仮選択(ﾎﾝﾁｬﾝはﾏｲﾍﾟｰｼﾞで)、予約・貸出書籍の確認、予約書籍のｷｬﾝｾﾙができる。
class ResultView(PaginationMixin,TemplateView):
    model = BookModel
    template_name = 'result.html'   
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        # メイン画面のかんたん検索の入力文字を取得。最後の"?"を除く。
        all_text = self.kwargs['kensaku'][:-1] # ﾊﾟｲｿﾝ|5|21|19|<Page 1 of 2>4　(?を除去)
        all_text_member =  all_text.split('|') # ['ﾊﾟｲｿﾝ', '5', '21', '19', '<Page 1 of 2>4']
        key_word = all_text_member[0]          # ﾊﾟｲｿﾝ
        # MeCabによる形態素解析-----------------------------------------------------------
        key_word = key_word.replace("","") # 半角ｽﾍﾟｰｽ削除
        def mecab_list(key_word):
            tagger = MeCab.Tagger()
            #tagger = MeCab.Tagger("-Ochasen")
            tagger.parse('')
            node = tagger.parseToNode(key_word)
            word_class = []
            while node:
                word = node.surface
                wclass = node.feature.split(',')
                if wclass[0] != u'BOS/EOS':
                    if wclass[6] == None:
                        word_class.append((word,wclass[0],wclass[1],wclass[2],""))
                    else:
                        word_class.append((word,wclass[0],wclass[1],wclass[2],wclass[6]))
                node = node.next
            word_class2 = []
            # MeCabで助詞を除いたキーワードを作成。(主に名詞、動詞)
            word_class2 = [i[0] for i in word_class if '助詞' not in i[1]]
            return word_class2
        #---------------------------------------------------------------------------------
        keyword = mecab_list(key_word)
        # MeCabの形態素解析の結果を、「ひらがな ⇒ カタカナ ⇒ 半角(ｶﾀｶﾅ)」に変換。 ※BookModelのｷｰﾜｰﾄﾞ(book3)を半角の英数、ｶﾅとする。
        keyword_list = []
        for i in keyword:        
            kword = jaconv.hira2hkata(i)       # ひらがな⇒カタカナ
            kword = mojimoji.zen_to_han(kword) # 全角⇒半角
            kword = kword.lower()              # 大文字⇒小文字
            keyword_list.append(kword)
        #keyword_list = keyword
        # 整形したｷｰﾜｰﾄﾞ(keyword_list)でfilterし、検索。
        for i in range(len(keyword_list)):
            if i==0:
                result = BookModel.objects.filter(book3__icontains=keyword_list[i])
                result = result.filter(book3__icontains=keyword_list[i])
            else:
                result = result.filter(book3__icontains=keyword_list[i])
        # ソートの種類を取得。
        sort_order = int(all_text_member[-1][-1]) #['ﾊﾟｲｿﾝ', '5', '21', '19', '<Page 1 of 2>4'] ⇒ 4
        # 現在のページを取得。
        page = self.request.GET.get('page')
        # userを設定。
        if self.request.user.is_anonymous:
            user = 0
        else:
            user = self.request.user
        # ページネーション ----------------------------------------------------------------
        jobs,reserved_list,sort_order,borrow_list,book_list = paginator.pagination(all_text,result,page,sort_order,user)
        #--------------------------------------------------------------------------------
        kensaku = '|'.join(all_text.split('|')[:-1]) # ﾊﾟｲｿﾝ|5|21|19|<Page 1 of 2>4 ⇒　ﾊﾟｲｿﾝ|5|21|19
        if kensaku == "":
            kensaku = all_text
        context['num'] = [int(i) for i in all_text_member[1:-1]] #予約の仮選択した書籍のNo.。　ﾏｲﾍﾟｰｼﾞにて正式に予約手続き。
        context['jobs'] = jobs                   #ﾍﾟｰｼﾞﾈｰｼｮﾝのﾍﾟｰｼﾞ番号　 <Page 1 of 6>
        context['sort_order'] = sort_order       #sort_order:ｿｰﾄ種類
        context['kensaku'] = kensaku             # かんたん検索の入力文字
        context['reserved_list'] = reserved_list #予約済の書籍No.
        context['borrow_list'] = borrow_list     #貸出中の書籍No.
        context['book_list'] = book_list         #予約&貸出中の書籍ﾃﾞｰﾀ
        return context
    def post(self,request,*args,**kwargs):
        context = super().get_context_data(**kwargs)
        # 選択ボタンの検出 ------------------------------------
        try:
            choice = request.POST['choice']          # 検索文字、予約の仮選択した書籍No.、ページ情報。例：python|5+17+<Page 2 of 6>2?
            orignal = choice.split('+')              # choiceを"+"で分割し、orignalへ。
            original_marge = '|'.join(orignal)       # choiceの記載を変換。　例：python|5|17|<Page 2 of 6>2?
            all_items = []                           # all_items ：選択のする・しないを繰り返した際の、重複を排除。
            item_l = original_marge.split('|')[1:-1] # 予約の仮選択した書籍No.のﾘｽﾄ　例：['5', '17']
            # all_items ：選択のする・しないを繰り返した際の、重複を排除。
            for i in item_l:
                if i not in all_items:
                    all_items.append(i)
                else:
                    all_items.remove(i)
            # kensakuの作成。
            if all_items == []:
                kensaku = orignal[0].split('|')[0] + '|' + orignal[2] #kensaku = orignal[0]
            else:
                kensaku = orignal[0].split('|')[0] + '|' + '|'.join(all_items) + '|'+ orignal[2]
            context['kensaku'] = kensaku
            return redirect('result',kensaku)
        except:
            print('---no_choice----')
        # 登録ボタンの検出 ------------------------------------
        try:
            reservation = self.request.POST['reservation']
            if reservation.find('|') > 0 :
                reservation += '|<Page 1 of 1>2' #ﾍﾟｰｼﾞﾈｰｼｮﾝの画面遷移と合わせるため、'|<Page 1 of 1>2?'を追加。
                return redirect('reservation',reservation)
            else:
                reservation += '|<Page 1 of 1>2' #ﾍﾟｰｼﾞﾈｰｼｮﾝの画面遷移と合わせるため、'|<Page 1 of 1>2?'を追加。
                return redirect('reservation',reservation)
                #return redirect('main')
        except:
            print('---no_reserve---')
        # Prevボタンの検出------------------------------------
        try:
            prev = request.POST['prev'] #ソートボタンの検出
            # prevからの"&&"を削除。
            kensaku = prev.split('&&')[0] + prev.split('&&')[1] + '?' # 例：python|5|17|<Page 1 of 2>4?
        except:
            print('---no_prev---')
        # cancelの検出 -----------------------------------------
        try:
            cancel = request.POST['cancel'] #キャンセルボタンの検出
            cancel_list = cancel.split('+')
            book = ReservationModel.objects.get(user=self.request.user,book__book=cancel_list[1])
            book.delete()
            kensaku = cancel_list[0] + '|<Page 1 of 1>2?'
            other_reservation = ReservationModel.objects.filter(book__book=cancel_list[1])
        except:
            print('---no_cancel---')
        #------------------------------------------------------
        return redirect('result',kensaku)

### マイページ画面(reservation)の表示。予約ができる。予約・貸出書籍（自・他）の確認、また、予約書籍のｷｬﾝｾﾙができる。
class ReservationView(LoginRequiredMixin,TemplateView):
    template_name = 'reservation.html'
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        all_text = self.kwargs['reservation']     # ﾊﾟｲｿﾝ|5|21|19|4|1|2%5%21%<Page 1 of 2>2
        all_text_member = all_text.split('%')     # ['ﾊﾟｲｿﾝ|5|21|19|4|1|2', '5', '21', '<Page 1 of 2>2']
        num = all_text_member[0].split('|')[1:]   # ['5', '21', '19', '4', '1', '2' , '<Page 1 of 2>4']
        num =[int(i) for i in num if i.isdigit()] # [5, 21, 19, 4, 1, 2]　予約の仮選択No.のリスト（isdigitで、文字列が数値のみ）
        result = []
        for book in num:
            result += BookModel.objects.filter(id=book)
        # ソートの種類を取得。
        sort_order = int(all_text_member[-1][-1]) # ['ﾊﾟｲｿﾝ|5|21|19|4|1|2', '5', '21', '<Page 1 of 2>2'] --> 2
        # 現在のページを取得。
        page = self.request.GET.get('page')
        user=self.request.user
        # ﾍﾟｰｼﾞﾈｰｼｮﾝ ------------------------------------------
        jobs,reserved_list,sort_order,borrow_list,book_list = paginator.pagination(all_text,result,page,sort_order,user)
        #-----------------------------------------------------
        try:
            all_text_member_int = [int(i) for i in all_text_member[1:-1]] #['ﾊﾟｲｿﾝ|5|21|19|4|1|2', '5', '21', '<Page 1 of 2>2'] --> [5,21]            
            for i in all_text_member_int:
                if i in num:
                    num.remove(i)
                else:
                    num.append(i)
        except:
            print('ng')
        if '%' not in all_text:
            delete_book = []
            for i in borrow_list:
                if i in num:
                    delete_book.append(str(i))
            for i in reserved_list:
                if i in num:
                    delete_book.append(str(i))
            delete_b = '%'.join(delete_book)
            all_text2 = all_text.split('<')
            all_text = all_text2[0] + '%' + delete_b + '%<' + all_text2[1]
        context['num'] = num                     #予約の仮選択した書籍のNo.。　ﾏｲﾍﾟｰｼﾞにて正式に予約手続き。
        context['jobs'] = jobs                   #ﾍﾟｰｼﾞﾈｰｼｮﾝのﾍﾟｰｼﾞ番号　 <Page 1 of 6>
        context['sort_order'] = sort_order       #sort_order:ｿｰﾄ種類
        context['kensaku'] = all_text            # かんたん検索の入力文字
        context['reserved_list'] = reserved_list #予約済の書籍No.
        context['borrow_list'] = borrow_list     #貸出中の書籍No
        context['book_list'] = book_list         #予約&貸出中の書籍ﾃﾞｰﾀ
        return context
    def post(self,request,*args,**kwargs):
        context = super().get_context_data(**kwargs)
        # 選択ボタンの検出 ---------------------------------------------
        try:
            orignal = (request.POST['choice']).split('+')
            orignal_first = orignal[0].split('<')[0]
            if orignal_first[-1] != '%':
                orignal_first += '%'
            kensaku = orignal_first + orignal[1] + '%' + orignal[2]
            context['kensaku'] = kensaku
            return redirect('reservation',kensaku)
        except:
            print('---R_no_choice---')
        # 登録ボタンの検出 ----------------------------------------------
        try:
            reservation = request.POST['reservation']      #ﾊﾟｲｿﾝ|5|21|19|4|1|2%5%21%<Page 1 of 2>2
            reservation_list = reservation.split('|')[1:-1]#[5,21,19,4,1]
            non_reservation = reservation.split('%')[1:-1] #[5,21]
            for i in non_reservation:
                if i in reservation_list:
                    reservation_list.remove(i)             #[19,4,1]  5,21,  [21,19,4,1]  5,   
                else:
                    if i != "":
                        reservation_list.append(i)         #もし　non-resが[5,21､5]なら　5　復活
            for i in reservation_list:                     #[19,4,1]
                res_book = BookModel.objects.get(id =i)
                today = datetime.date.today()              #status=1がなければ、他に予約はなく、status=1で登録
                reservation_number = ReservationModel.objects.filter(book=res_book,status="1").count()
                if reservation_number==0:
                    ReservationModel.objects.create(book=res_book,reservation_date=today,user=self.request.user,status=1)
                else:
                    ReservationModel.objects.create(book=res_book,reservation_date=today,user=self.request.user)
            return redirect('logout')
        except:
            print('---R_no_reserve---')
        # Prevボタンの検出 --------------------------------------------
        try:
            prev = request.POST['prev']
            kensaku = prev.split('&&')[0]
            kensaku_part = kensaku.split('<')
            if len(kensaku_part) > 2:
                kensaku = kensaku_part[0]+ '<' + kensaku_part[-1] + prev.split('&&')[1]
        except:
            print('---R_no_prev----')
            sort_order = 2
        # キャンセルボタンの検出 ---------------------------------------
        try:
            cancel = request.POST['cancel']
            cancel = cancel.split('+')
            # キャンセルされた本の予約総数
            reservation_number = ReservationModel.objects.filter(book__book=cancel[1]).count()
            # キャンセルされた本は取置き本、また、取置き数
            reserving_book = ReservationModel.objects.filter(book__book=cancel[1],status="T") ### 取り置き本（0か1）
            reserving_book = [i.id for i in reserving_book]
            reserving_book_number = len(reserving_book)
            # キャンセルされた本は貸出しているか、また、その総数（0か1）
            rented_book = ReservationModel.objects.filter(book__book=cancel[1],start_date__gt="2000-01-01") ### その本の貸出している書籍
            rented_book = [i.id for i in rented_book]
            rented_number = len(rented_book)
            book = ReservationModel.objects.get(user=self.request.user,book__book=cancel[1])
            book.delete()
            kensaku = cancel[0]
            if reservation_number - reserving_book_number - rented_number > 1 :
                reserving = ReservationModel.objects.filter(book__book=cancel[1])
                reserving_list = [i.id for i in reserving if i.id not in rented_book]
                reserving_list = [i.id for i in reserving if i.id not in reserving_book]
                reserving_list.sort()
                book = ReservationModel.objects.get(id=reserving_list[0],book__book=cancel[1])
                book.status = 1
                book.save()
            else:
                print('nothing')
        except:
            print('---R_no-cancel---')
        return redirect('reservation',kensaku)#,sort_order) 

### メインに表示する情報　----------------------------------------------
class InformationView(TemplateView):
    template_name = 'information.html'

### 過去の貸出し履歴を表示 ---------------------------------------------
class HistoryView(ListView):
    template_name = 'history.html'
    model = HistoryModel
    def get_context_data(self,*args,**kwargs):
        context = super().get_context_data(**kwargs)
        kensaku = self.kwargs['kensaku']
        object_list = HistoryModel.objects.filter(user=self.request.user)
        context['kensaku'] = kensaku
        context['object_list'] = object_list
        return context 
    
### Login -----------------------------------------------------------
class LoginView(auth_views.LoginView):
    template_name='login.html'
    form_class = LoginForm

### Logout ----------------------------------------------------------
class LogoutView(LoginRequiredMixin,LogoutView):
    template_name= 'logout.html'

#################### 以下、管理者用 #######################################################
# 貸出し・返却:ユーザーを設定後、貸出し・返却を行なう。貸出しは5冊まで。
#             取置きが有る場合、返却する本に予約があり取置きが必要な場合を、管理者に知らせる。
class RentView(UserPassesTestMixin,TemplateView):
    template_name = 'rent.html'
    model = ReservationModel
    def test_func(self):
        return self.request.user.is_staff
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        try:
            userid = self.kwargs['userid']
            user = CustomUser.objects.get(username=userid)
            reserved_books = ReservationModel.objects.filter(user=user)
            reserved_books_list = [[i.book.book,i.book.author.author,i.book.publisher.publisher,\
                i.limited_date,i.end_date] for i in reserved_books]
            for i in reserved_books_list:
                res = ReservationModel.objects.filter(user=user,book__book=i[0],start_date__gt="2000-01-01")
                res_list = [i.book for i in res]
                for j in res_list:
                    if ReservationModel.objects.filter(book__book=j).count() > 1:
                        i[3] = "t"
            rent_book = ReservationModel.objects.filter(user=user,start_date__gt="2000-01-01")
            rent_book = [i.book.book for i in rent_book]
            context["book_list"] = reserved_books_list
            context["userid"] = userid
            context["rent_book"] = rent_book
            return context
        except:
            print('---Rent_ng---')
            return
    def post(self,request,*args,**kwargs):
        context = super().get_context_data(**kwargs)
        # ユーザ設定：ユーザIDを入力し、対象者を決める#####
        try:
            userid = request.POST['userid']
            return redirect('rent',userid)
        except:
            print('--Rent_ng_userid--')
        # 貸出し・返却　---------------------------------
        try:
            rent_book = request.POST['book']
            userid = request.POST['reservation']
            user = CustomUser.objects.get(username=userid)
            rent_book_number = ReservationModel.objects.filter(user=user,start_date__gt="2000-01-01").count()#貸出している書籍の数
            rented_book_number = ReservationModel.objects.filter(book__book=rent_book,start_date__gt="2000-01-01").count()#書籍の貸出し数（1か0）
            reserving_book_number = ReservationModel.objects.filter(user=user,book__book=rent_book,status="T").count()
            today = datetime.date.today()
            day_after_tomorrow = datetime.timedelta(days=14)
            end_day = today + day_after_tomorrow
            rented_book = BookModel.objects.get(book=rent_book)
            # 返却：貸出し書籍の数=１。　貸出していた本、つまり返却。予約から削除し、履歴に移動。
            if  rented_book_number == 1:
                rented_book = ReservationModel.objects.get(book=rented_book ,user=user)
                rented_book.delete()
                book = HistoryModel.objects.create(book=rented_book , start_day=rented_book.start_date, end_day=rented_book.end_date, user=user)
            # 貸出し(取り置きしたいた本)　取り置き期限、status=T を削除。#
            elif rent_book_number < 5 and reserving_book_number == 1:
                book = ReservationModel.objects.get(book=rented_book ,user=user)
                book.start_date = today
                book.end_date = end_day
                book.limited_date = None
                book.status = None
                book.save()
            # 貸出し ------------------------------------
            #　 予約をしたが、直ぐに図書館の書棚の本を持って、受付で予約する場合。(予約を削除)                                           ######
            #　 同じユーザは、特定の本の予約は、１つしかできない。（既に予約がある本は、マイページでボタンが【予約済】となり予約ができない）######
            #　 取置き済みの本を、他のユーザが受付で貸出しはできない。                                                                  ######
            elif rent_book_number < 5 and  rented_book_number == 0:
                try:
                    rent_book = BookModel.objects.get(book=rent_book)
                    reserved_book = ReservationModel.objects.get(book=rent_book,user=user)
                    reserved_book.delete()
                except:
                    print('ng2')
                rent_book = BookModel.objects.get(book=rent_book)
                book = ReservationModel.objects.create(book=rent_book,start_date=today,end_date=end_day,user=user)
                return redirect('rent',userid)
        except:
            print('--ng--')
        return redirect('rent',userid)

### 予約本の取置き：取り置きの対象、取り置き期限切れを管理者に知らせる。
class ReservingView(UserPassesTestMixin,TemplateView):
    template_name = 'reserving.html'
    model = ReservationModel
    def test_func(self):
        return self.request.user.is_staff
    def get_context_data(self,*args,**kwargs):
        context = super().get_context_data(**kwargs)
        # 貸出している本 
        borrowed_book = ReservationModel.objects.filter(start_date__gt="2000-01-01")
        borrowed_books = [i.book.book for i in borrowed_book]  
        # 取置き済みの本 
        reserved_book = ReservationModel.objects.filter(status='T') 
        reserved_books = [i.book.book for i in reserved_book] 
        # 貸出しや取置き済みの本。reserving_list作成のためにまとめる。 
        borrowed_reserved_books = borrowed_books + reserved_books 
        # 取置きの対象：貸出しや取置きをしていない、取置きのstatusが"1"のリスト。 
        reserving = ReservationModel.objects.filter(status="1")
        reserving_list = [[i.book.book,i.book.author.author,i.book.publisher.publisher,\
            i.book.year,i.user.username,0] for i in reserving if i.book.book not in borrowed_reserved_books]
        context["book_list"] = reserving_list 
        # 取置き済み本：取置き期限が切れキャンセル対象となる予約を管理者に知らせる 
        reserved = ReservationModel.objects.filter(status="T")
        reserved_list = [[i.book.book,i.book.author.author,i.book.publisher.publisher,\
            i.limited_date,i.user.username,0] for i in reserved ]
        context["reserved_list"] = reserved_list
        return context
    def post(self,request,*args,**kwargs):
        context = super().get_context_data(**kwargs)
        # 管理者は、取り置き対象の本を、書棚から持ち帰った際、取置きボタンにて、取置きを行なう。
        # 取置き後は、予約データのstatusを"T"、取り置き期限を1週間後、変更する。
        # また、他に予約があれば、最も速い予約(idが小さい）のstatusを"1"に、変更する。（sort後、[0]を対象にする)
        try:
            implement = request.POST['implement']
            book = ReservationModel.objects.get(book__book=implement,status=1)
            book.status = "T" ###"T"は取置き済みを示す。
            today = datetime.date.today()
            limited_day = datetime.timedelta(days=7)
            book.limited_date = today + limited_day
            book.save()
            # 他予約があれば、最も速い予約のstausを"1"に変更 
            other_book = ReservationModel.objects.filter(book__book=implement)
            other_book = [i.id for i in other_book if i.id != book.id]
            other_book.sort()
            if len(other_book)>0:
                book = ReservationModel.objects.get(id=other_book[0])
                book.status = "1" #　"1"は、最も速い予約を示す。
                book.save()
            return redirect('reserving')
        except:
            print('ng')
        # 取置き期限切れの予約を削除する。 その際、他に予約があれば、最も速い予約のstatusを"1"に変更する。      
        try:
            cancel = request.POST['cancel']
            book = ReservationModel.objects.get(book__book=cancel,status="T")
            book.delete()
            # 対象の全予約他→に予約があれば、最も速い予約のstatusを"1"に変更する 
            other_book = ReservationModel.objects.filter(book__book=cancel)
            other_book = [i.id for i in other_book if i.id != book.id]
            other_book.sort()
            if len(other_book)>0:
                book = ReservationModel.objects.get(id=other_book[0])
                book.status = "1"
                book.save()
            return redirect('reserving')
        except:
            print('ng')

### メインで表示する情報の一覧 
class CommentView(UserPassesTestMixin,ListView):
    model = CommentModel
    template_name = 'comment.html'
    def test_func(self):
        return self.request.user.is_staff
    
### メインで表示する情報の一覧の作成 
class CreateView(UserPassesTestMixin,CreateView):
    template_name = 'create.html'
    model =  CommentModel
    fields = ['comment','status']
    success_url = reverse_lazy('comment')
    def test_func(self):
        return self.request.user.is_staff
    
### メインで表示する情報の一覧の編集 
class UpdateView(UserPassesTestMixin,UpdateView):
    template_name = 'update.html'
    model = CommentModel
    fields = ['comment','status']
    success_url = reverse_lazy('comment')
    def test_func(self):
        return self.request.user.is_staff
    
### メインで表示する情報の一覧の削除 
class DeleteView(UserPassesTestMixin,DeleteView):
    template_name = 'delete.html'
    model = CommentModel
    success_url = reverse_lazy('comment') 
    def test_func(self):
        return self.request.user.is_staff