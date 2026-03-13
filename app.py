import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import traceback

# Загружаем данные
df = pd.read_csv('pyaterochka_reviews_with_sentiment.csv')

# Добавим колонку с городом
df['city'] = df['address'].str.extract(r'^([^,]+)')

# Инициализируем приложение
app = dash.Dash(__name__)
app.title = "Анализ отзывов Пятёрочка"

# Описываем layout
app.layout = html.Div([
    html.H1("Анализ отзывов Пятёрочка", 
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
    
    # Фильтры
    html.Div([
        html.Div([
            html.Label("Выберите город:"),
            dcc.Dropdown(
                id='city-dropdown',
                options=[{'label': 'Все города', 'value': 'all'}] + 
                        [{'label': city, 'value': city} for city in df['city'].dropna().unique()],
                value='all'
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label("Диапазон рейтинга:"),
            dcc.RangeSlider(
                id='rating-slider',
                min=1,
                max=5,
                step=0.5,
                value=[1, 5],
                marks={1: '1', 2: '2', 3: '3', 4: '4', 5: '5'}
            )
        ], style={'width': '60%', 'display': 'inline-block', 'padding': '10px'})
    ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'}),
    
    # Карточки с метриками
    html.Div([
        html.Div([
            html.H4("Всего отзывов", style={'fontSize': '16px', 'marginBottom': '5px'}),
            html.H2(id='total-reviews', style={'color': '#3498db', 'fontSize': '28px', 'margin': '5px 0'})
        ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'width': '20%', 'display': 'inline-block',
                'textAlign': 'center', 'verticalAlign': 'top', 'marginRight': '2%'}),
        
        html.Div([
            html.H4("Средний рейтинг", style={'fontSize': '16px', 'marginBottom': '5px'}),
            html.H2(id='avg-rating', style={'color': '#2ecc71', 'fontSize': '28px', 'margin': '5px 0'})
        ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'width': '20%', 'display': 'inline-block',
                'textAlign': 'center', 'verticalAlign': 'top', 'marginRight': '2%'}),
        
        html.Div([
            html.H4("Позитивных", style={'fontSize': '16px', 'marginBottom': '5px'}),
            html.H2(id='positive-pct', style={'color': '#2ecc71', 'fontSize': '28px', 'margin': '5px 0'})
        ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'width': '20%', 'display': 'inline-block',
                'textAlign': 'center', 'verticalAlign': 'top', 'marginRight': '0'}),
        
        html.Div([
            html.H4("Негативных", style={'fontSize': '16px', 'marginBottom': '5px'}),
            html.H2(id='negative-pct', style={'color': '#e74c3c', 'fontSize': '28px', 'margin': '5px 0'})
        ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'width': '20%', 'display': 'inline-block',
                'textAlign': 'center', 'verticalAlign': 'top'})
    ], style={'marginBottom': '30px', 'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-between'}),
    
    # Графики
    html.Div([
        html.Div([
            dcc.Graph(id='sentiment-pie')
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='sentiment-hist')
        ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
    ]),
    
    html.Div([
        html.Div([
            dcc.Graph(id='rating-boxplot')
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='city-bar')
        ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
    ]),
    
    # Таблица с примерами отзывов
    html.Div([
        html.H3("📝 Примеры отзывов", style={'marginTop': '30px', 'marginBottom': '10px'}),
        dash_table.DataTable(
            id='reviews-table',
            columns=[
                {'name': 'Отзыв', 'id': 'text'},
                {'name': 'Рейтинг', 'id': 'rating'},
                {'name': 'Тональность', 'id': 'sentiment'},
                {'name': 'Город', 'id': 'city'}
            ],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            page_size=10
        )
    ])
])

# Функции для обновления графиков
@app.callback(
    [Output('total-reviews', 'children'),
     Output('avg-rating', 'children'),
     Output('positive-pct', 'children'),
     Output('negative-pct', 'children'),
     Output('sentiment-pie', 'figure'),
     Output('sentiment-hist', 'figure'),
     Output('rating-boxplot', 'figure'),
     Output('city-bar', 'figure'),
     Output('reviews-table', 'data')],
    [Input('city-dropdown', 'value'),
     Input('rating-slider', 'value')]
)
def update_dashboard(selected_city, rating_range):
    try:
        # Фильтруем данные
        filtered_df = df.copy()
        
        # если selected_city None или 'all', не фильтруем по городу
        if selected_city and selected_city != 'all' and selected_city != 'None':
            filtered_df = filtered_df[filtered_df['city'] == selected_city]
        
        # Фильтр по рейтингу
        filtered_df = filtered_df[
            (filtered_df['rating'] >= rating_range[0]) & 
            (filtered_df['rating'] <= rating_range[1])
        ]
        
        if len(filtered_df) == 0:
            empty_fig = px.pie(title="Нет данных для отображения")
            return "0", "0.00", "0%", "0%", empty_fig, empty_fig, empty_fig, empty_fig, []
        
        # Метрики
        total = len(filtered_df)
        avg_rating = filtered_df['rating'].mean()
        positive_pct = (filtered_df['sentiment'] == 'positive').mean() * 100
        negative_pct = (filtered_df['sentiment'] == 'negative').mean() * 100
        
        # Круговая диаграмма тональности
        pie_fig = px.pie(
            filtered_df, 
            names='sentiment',
            title='Распределение тональности',
            color='sentiment',
            color_discrete_map={'positive': '#2ecc71', 'neutral': '#95a5a6', 'negative': '#e74c3c'}
        )
        
        # Гистограмма распределения тональности
        hist_fig = px.histogram(
            filtered_df,
            x='sentiment_score',
            title='Распределение тональности (от -1 до 1)',
            nbins=50,
            color_discrete_sequence=['#3498db']
        )
        
        # Рейтинг по тональности
        box_fig = px.box(
            filtered_df,
            x='sentiment',
            y='rating',
            title='Связь тональности и рейтинга',
            color='sentiment',
            color_discrete_map={'positive': '#2ecc71', 'neutral': '#95a5a6', 'negative': '#e74c3c'}
        )
        
        # Топ-10 городов по количеству отзывов
        city_stats = filtered_df['city'].value_counts().head(10).reset_index()
        city_stats.columns = ['city', 'count']
        bar_fig = px.bar(
            city_stats,
            x='count',
            y='city',
            title='Топ-10 городов по количеству отзывов',
            orientation='h',
            color_discrete_sequence=['#3498db']
        )
        
        # Данные для таблицы
        table_df = filtered_df.head(20).copy()
        table_df['text_short'] = table_df['text'].str[:100] + '...'
        table_data = table_df[['text_short', 'rating', 'sentiment', 'city']].rename(
            columns={'text_short': 'text'}
        ).to_dict('records')
        
        return (
            f"{total:,}", f"{avg_rating:.2f}", f"{positive_pct:.1f}%", f"{negative_pct:.1f}%",
            pie_fig, hist_fig, box_fig, bar_fig, table_data
        )
        
    except Exception as e:
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Описание ошибки: {str(e)}")
        traceback.print_exc()
        empty_fig = px.pie(title="Ошибка загрузки данных")
        return "0", "0.00", "0%", "0%", empty_fig, empty_fig, empty_fig, empty_fig, []

# Запускаем приложение
if __name__ == '__main__':
    app.run(debug=True)