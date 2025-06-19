const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  mode: 'development',
    entry: {
        home: './client/pages/users-home.js',
        userSettings: './client/pages/user-settings.js',
        quickstart: './client/pages/quickstart.js',
        exampleLibrary: './client/pages/example-library.js',
        browser: './client/pages/browser.js',
        editor: './client/pages/model-editor.js',
        domainEditor: './client/pages/domain-editor.js',
        workflowSelection: './client/pages/workflow-selection.js',
        workflowEditor: './client/pages/workflow-manager.js',
        projectManager: './client/pages/project-manager.js',
        loadingPage: './client/pages/loading-page.js',
        multiplePlots: './client/pages/multiple-plots.js'
    },
  output: {
    filename: 'model_builder-[name].bundle.js',
    path: path.resolve(__dirname, "model_builder/dist")
  },
  devtool: 'inline-source-map',
  plugins: [
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Home',
      filename: 'model_builder-user-home.html',
      template: 'page_template.pug',
      name: 'home',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | User Settings',
      filename: 'model_builder-user-settings.html',
      template: 'page_template.pug',
      name: 'userSettings',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Quickstart',
      filename: 'model_builder-quickstart.html',
      template: 'page_template.pug',
      name: 'quickstart',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Example Library',
      filename: 'model_builder-example-library.html',
      template: 'page_template.pug',
      name: 'exampleLibrary',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Model Browser',
      filename: 'model_builder-file-browser.html',
      template: 'page_template.pug',
      name: 'browser',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Model Editor',
      filename: 'model_builder-model-editor.html',
      template: 'page_template.pug',
      name: 'editor',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Domain Editor',
      filename: 'model_builder-domain-editor.html',
      template: 'page_template.pug',
      name: 'domainEditor',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Workflow Selection',
      filename: 'model_builder-workflow-selection.html',
      template: 'page_template.pug',
      name: 'workflowSelection',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Workflow Editor',
      filename: 'model_builder-workflow-manager.html',
      template: 'page_template.pug',
      name: 'workflowEditor',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'GillesPy3D | Project Manager',
      filename: 'model_builder-project-manager.html',
      template: 'page_template.pug',
      name: 'projectManager',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: "GillesPy3D | Loading Page",
      filename: 'model_builder-loading-page.html',
      template: 'page_template.pug',
      name: 'loadingPage',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: "GillesPy3D | Multiple Plots Page",
      filename: 'multiple-plots-page.html',
      template: 'page_template.pug',
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
