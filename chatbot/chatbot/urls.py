from django.urls import path
from django.views.generic import RedirectView
from . import views as views

urlpatterns = [
    path('',          RedirectView.as_view(pattern_name='dashboard'), name='chatbot_root'),
    path('login/',    views.login_view,  name='login'),
    path('logout/',   views.logout_view, name='logout'),
    path('dashboard/', views.dashboard,  name='dashboard'),
    path('chat/',     views.chatbot,     name='chatbot'),

    # 사용자 관리
    path('users/',                    views.user_list,   name='user_list'),
    path('users/add/',                views.user_add,    name='user_add'),
    path('users/<int:user_id>/edit/', views.user_edit,   name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),

    # 로그 관리
    path('logs/', views.log_history, name='log_history'),

    # 채팅 API
    path('chat/rags/',                               views.chat_rags,             name='chat_rags'),
    path('chat/api/',                                views.chat_api,              name='chat_api'),
    path('chat/sessions/',                           views.chat_sessions,         name='chat_sessions'),
    path('chat/session/<uuid:session_uuid>/messages/', views.chat_session_messages, name='chat_session_messages'),

    # 대시보드 API
    path('dashboard/rags/',                   views.dashboard_rags,  name='dashboard_rags'),
    path('dashboard/stats/',                  views.dashboard_stats,  name='dashboard_stats'),
    path('dashboard/charts/',                 views.dashboard_charts, name='dashboard_charts'),

    # 분석 및 통계
    path('analytics/',           views.chart_list,    name='chart_list'),
    path('analytics/data/',      views.analytics_data, name='analytics_data'),

    # 문서 관리 (어드민)
    path('docs/',                views.doc_list,   name='doc_list'),
    path('docs/<int:doc_id>/',   views.doc_detail, name='doc_detail'),

    # 채팅 세션 관리 (어드민)
    path('chatting/',                       views.chatting_list,  name='chatting_list'),
    path('chatting/count/',                 views.chatting_count, name='chatting_count'),
    path('chatting/<uuid:session_uuid>/',   views.chatting_view,  name='chatting_view'),

    # RAG 설정
    path('rag/',                              views.rag_setting,     name='rag_setting'),
    path('rag/add/',                          views.rag_add,         name='rag_add'),
    path('rag/<int:rag_id>/edit/',            views.rag_edit,        name='rag_edit'),
    path('rag/<int:rag_id>/delete/',          views.rag_delete,      name='rag_delete'),
    path('rag/<int:rag_id>/build/',           views.rag_build,       name='rag_build'),
    path('rag/<int:rag_id>/status/',          views.rag_build_status, name='rag_build_status'),
]
