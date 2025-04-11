update_layout_kwargs = dict(
    title=dict(font_size=30, font_color='rgb(189, 198, 56)', x=0.5,),
    font=dict(color='rgb(0, 50, 105)', family='Arial',),
    margin=dict(b=10, l=10, r=10, t=60,),
    height=600,
    separators=',.',
    paper_bgcolor='rgba(0, 0, 0, 0)',
    plot_bgcolor='rgba(0, 0, 0, 0)',
    legend=dict(orientation='h', title=dict(side='top')),

    yaxis=dict(tickformat=',.2s', gridcolor='rgba(189, 198, 56, 0.5)', zerolinecolor="rgba(0, 50, 105, 0.2)",),
    xaxis=dict(gridcolor='rgba(189, 198, 56, 0.5)',),
)

update_traces_kwargs = dict(
    texttemplate='%{text:.2s}',
)
