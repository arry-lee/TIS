import pathlib
p ='../config/financial_statement_config.yaml'

p = pathlib.Path(p)
with p.open('r',encoding='utf-8') as f:
    print(f.read())