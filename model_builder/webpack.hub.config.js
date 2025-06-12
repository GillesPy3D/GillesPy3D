const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  mode: 'development',
  entry: {
    home: './client/pages/home.js',
    jobPresentation: './client/pages/job-presentation.js',
    modelPresentation: './client/pages/model-presentation.js',
    notebookPresentation: './client/pages/notebook-presentation.js',
    multiplePlots: './client/pages/multiple-plots.js'
  },
  output: {
    filename: 'model_builder-[name].bundle.js',
    path: path.resolve(__dirname, 'jupyterhub/static')
  },
  devtool: 'inline-source-map',
  plugins: [
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Home',
      filename: '../templates/model_builder-home.html',
      template: 'jupyterhub/home_template.pug',
      name: 'home',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Job Presentation',
      filename: '../templates/model_builder-job-presentation.html',
      template: 'jupyterhub/home_template.pug',
      name: 'jobPresentation',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Model Presentation',
      filename: '../templates/model_builder-model-presentation.html',
      template: 'jupyterhub/home_template.pug',
      name: 'modelPresentation',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Notebook Presentation',
      filename: '../templates/model_builder-notebook-presentation.html',
      template: 'jupyterhub/home_template.pug',
      name: 'notebookPresentation',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: "GillesPy3D | Multiple Plots Presentation Page",
      filename: '../templates/multiple-plots-page.html',
      template: 'jupyterhub/home_template.pug',
      name: 'multiplePlots',
      inject: false
    })
  ],
  optimization: {
    splitChunks: {
      cacheGroups: {
        commons: {
          name: 'common',
          chunks: 'initial',
          minChunks: 2
        }
      }
    }
  },
  module: {
    rules: [
      {
        test: /\.pug$/,
        use: [ 'pug-loader' ]
      },
      {
        test: /\.css$/,
        use: [
          'style-loader',
          'css-loader'
        ]
      },
      {
        test: /\.(png|svg|jpg|gif)$/,
        use: [
          'file-loader' 
        ]
      }
    ]
  }
}
