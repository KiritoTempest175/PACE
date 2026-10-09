import globals from 'globals';
import hooks from 'eslint-plugin-react-hooks';
export default [{files:['src/**/*.{js,jsx}'],languageOptions:{ecmaVersion:'latest',sourceType:'module',globals:{...globals.browser,...globals.es2022}},plugins:{'react-hooks':hooks},rules:{...hooks.configs.recommended.rules,'no-unused-vars':['warn',{argsIgnorePattern:'^_'}]}}];
